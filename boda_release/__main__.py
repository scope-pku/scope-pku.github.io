from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from . import (
    BodaAuthenticationError,
    BodaClient,
    BodaError,
    DEPLOYMENT_STATE_FILENAME,
    DeploymentState,
    DeploymentStateNotFound,
    Release,
    deploy_incremental,
    deploy_release,
    load_persistent_session,
    login_iaaa,
    publish_deployment_state,
    run_crud_test,
    save_persistent_session,
)


def _default_session_path(
    system: str | None = None,
    home: Path | None = None,
    xdg_cache_home: str | None = None,
) -> Path:
    system = system or sys.platform
    home = home or Path.home()
    xdg_cache_home = (
        os.environ.get("XDG_CACHE_HOME", "")
        if xdg_cache_home is None
        else xdg_cache_home
    )
    if xdg_cache_home:
        return Path(xdg_cache_home) / "bodacli" / "session.cookies"
    if system.lower() == "darwin":
        return home / "Library" / "Caches" / "bodacli" / "session.cookies"
    return home / ".cache" / "bodacli" / "session.cookies"


def _default_security_reason(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    now = now.astimezone(timezone.utc).replace(microsecond=0)
    return f"Published by bodacli at {now.strftime('%Y-%m-%dT%H:%M:%SZ')}."


@dataclass(frozen=True)
class GitSnapshot:
    commit: str
    dirty: bool
    changes: tuple[str, ...] = ()


def _git_snapshot(previous_commit: str | None = None) -> GitSnapshot:
    commit = _git_output("rev-parse", "--verify", "HEAD")
    dirty = bool(_git_output("status", "--porcelain=v1", "--untracked-files=all"))
    changes: tuple[str, ...] = ()
    if previous_commit is not None:
        if not _git_succeeds("cat-file", "-e", f"{previous_commit}^{{commit}}"):
            raise BodaError("Previous deployed commit is not available locally")
        if not _git_succeeds("merge-base", "--is-ancestor", previous_commit, commit):
            raise BodaError("Previous deployed commit is not an ancestor of HEAD")
        output = _git_output(
            "diff", "--name-status", "--find-renames", previous_commit, commit, "--"
        )
        changes = tuple(line for line in output.splitlines() if line)
    return GitSnapshot(commit, dirty, changes)


def _release_snapshot(
    release: Release, previous_commit: str | None = None
) -> GitSnapshot:
    snapshot = _git_snapshot(previous_commit)
    if release.source_commit is None or release.source_dirty is None:
        raise BodaError("Release is missing Git build metadata; rebuild it")
    if (
        release.source_commit != snapshot.commit
        or release.source_dirty != snapshot.dirty
    ):
        raise BodaError(
            "Release build metadata does not match the current Git worktree"
        )
    if snapshot.dirty:
        raise BodaError("Deployment requires a clean Git worktree")
    return snapshot


def _git_output(*arguments: str) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError as exc:
        raise BodaError("Git is unavailable") from exc
    if result.returncode != 0:
        raise BodaError("Git repository state could not be read")
    return result.stdout.strip()


def _git_succeeds(*arguments: str) -> bool:
    try:
        result = subprocess.run(
            ["git", *arguments],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise BodaError("Git is unavailable") from exc
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m boda_release")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="verify and print a release plan")
    plan.add_argument("release")

    probe = subparsers.add_parser("probe", help="verify the Boda session read-only")
    _add_remote_arguments(probe)

    deploy = subparsers.add_parser("deploy", help="upload a verified release")
    deploy.add_argument("release")
    deploy.add_argument("--incremental", action="store_true")
    deploy.add_argument("--apply", action="store_true")
    deploy.add_argument("--confirm")
    _add_remote_arguments(deploy)

    crud_test = subparsers.add_parser(
        "crud-test", help="run the disposable Boda CRUD smoke test"
    )
    crud_test.add_argument("--apply", action="store_true")
    crud_test.add_argument("--confirm")
    _add_remote_arguments(crud_test)

    args = parser.parse_args()
    try:
        if args.command == "plan":
            release = Release.load(args.release)
            print(f"Verified {len(release.files)} files:")
            for entry in release.files:
                print(entry.path)
            return 0
        if args.command == "crud-test":
            if not args.apply or args.confirm != "BODA_CRUD_TEST":
                raise BodaError("CRUD test requires --apply --confirm BODA_CRUD_TEST")
            client = _client(args)
            receipt_verified = run_crud_test(client)
            message = "CRUD test created, verified, and deleted A/B.txt."
            if not receipt_verified:
                message += (
                    " Upload receipt was non-JSON; directory listing verified the file."
                )
            print(message)
            return 0

        if args.command == "probe":
            client = _client(args)
            client.list_directory()
            print("Boda session and target root verified.")
            return 0

        confirmation = "DEPLOY_INCREMENTAL" if args.incremental else "DEPLOY_NONATOMIC"
        if not args.apply or args.confirm != confirmation:
            raise BodaError(f"Deployment requires --apply --confirm {confirmation}")
        release = Release.load(args.release)
        security_reason = _env("BODA_SECURITY_REASON") or _default_security_reason()
        client = _client(args)

        if args.incremental:
            try:
                previous = client.read_deployment_state()
            except DeploymentStateNotFound:
                listing = client.list_directory()
                if (
                    DEPLOYMENT_STATE_FILENAME in listing.files
                    or DEPLOYMENT_STATE_FILENAME in listing.folders
                ):
                    raise BodaError(
                        "Deployment state exists in Boda but is not publicly readable"
                    )
                snapshot = _release_snapshot(release)
                next_state = DeploymentState.from_release(
                    release,
                    commit=snapshot.commit,
                    dirty=False,
                    path_prefix=client.path_prefix,
                )
                count = deploy_release(client, release, security_reason)
                publish_deployment_state(client, next_state, security_reason)
                print(f"Bootstrapped incremental state with {count} uploaded files.")
                return 0

            snapshot = _release_snapshot(release, previous.commit)
            result = deploy_incremental(
                client,
                release,
                previous,
                snapshot.commit,
                security_reason,
            )
            print(
                f"Incremental deployment uploaded {result.uploaded}, "
                f"deleted {result.deleted}, kept {result.unchanged}; "
                f"Git reports {len(snapshot.changes)} changed paths."
            )
            return 0

        snapshot = _release_snapshot(release)
        next_state = DeploymentState.from_release(
            release,
            commit=snapshot.commit,
            dirty=False,
            path_prefix=client.path_prefix,
        )
        count = deploy_release(client, release, security_reason)
        publish_deployment_state(client, next_state, security_reason)
        print(f"Uploaded and verified {count} files; deployment state refreshed.")
        return 0
    except BodaError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _add_remote_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--path-prefix",
        default=os.getenv("BODA_PATH_PREFIX", ""),
        help="public and Boda directory prefix, for example /new",
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("BODA_BASE_URL", "https://boda.pku.edu.cn"),
    )
    parser.add_argument(
        "--public-url",
        default=os.getenv("BODA_PUBLIC_URL", "https://xulm.pku.edu.cn"),
    )


def _client(args: argparse.Namespace) -> BodaClient:
    session = load_persistent_session(
        _env("BODA_SESSION_FILE") or _default_session_path()
    )
    client = BodaClient(
        path_prefix=args.path_prefix,
        base_url=args.base_url,
        public_url=args.public_url,
        session=session,
    )
    if session.cookies:
        try:
            client.list_directory()
            return client
        except BodaAuthenticationError:
            pass

    login_iaaa(
        username=_env("BODA_IAAA_USERNAME"),
        password=_env("BODA_IAAA_PASSWORD"),
        otp_secret=_env("BODA_IAAA_OTP"),
        session=session,
    )
    client.list_directory()
    save_persistent_session(session)
    return client


def _env(name: str) -> str:
    if name in os.environ:
        return os.environ[name]
    path = Path(".env")
    if path.is_file():
        for line in path.read_text().splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() == name:
                value = value.strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                    return value[1:-1]
                return value
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
