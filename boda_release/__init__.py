"""Small, fail-closed client for Boda static releases."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import mimetypes
import os
import re
import tempfile
import time
from dataclasses import dataclass, field
from html.parser import HTMLParser
from http.cookiejar import LoadError, MozillaCookieJar
from pathlib import Path, PurePosixPath
from urllib.parse import quote, unquote, urlsplit
import requests


DEPLOYMENT_STATE_FILENAME = "bodacli-state.txt"
BUILD_METADATA_FILENAME = "BODACLI_BUILD.json"
_DEPLOYMENT_STATE_SCHEMA = 1
_BUILD_METADATA_SCHEMA = 1
_MAX_DEPLOYMENT_STATE_BYTES = 1024 * 1024
_MAX_BUILD_METADATA_BYTES = 4096
_RESERVED_DEPLOYMENT_PATHS = {
    DEPLOYMENT_STATE_FILENAME,
    BUILD_METADATA_FILENAME,
}


_CREATE_DIRECTORY_OK = "%E7%A1%AE%E5%AE%9A"
_IAAA_APP_ID = "bdwzqnews2025"
_IAAA_APP_NAME = "西安博达软件站群管理系统"
_IAAA_BASE_URL = "https://iaaa.pku.edu.cn"
_BODA_CAS_URL = "https://boda.pku.edu.cn/system/caslogin.jsp"
_SECURITY_UPDATE_RESPONSE_SHA256 = (
    "c77e5168dffda66b8dc13f1425b4d3630a6656a3e5acf707f4393277ba3c8b5e"
)


class BodaError(RuntimeError):
    """A safe, user-facing deployment error."""


class DeploymentStateNotFound(BodaError):
    """No deployment state has been published yet."""


class BodaUploadReceiptError(BodaError):
    """Boda accepted an upload but returned a non-JSON receipt."""


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


@dataclass(frozen=True)
class ReleaseFile:
    path: PurePosixPath
    sha256: str


class BodaAuthenticationError(BodaError):
    """The persisted Boda session is no longer authenticated."""


@dataclass(frozen=True)
class DeploymentState:
    commit: str
    dirty: bool
    path_prefix: str
    files: tuple[ReleaseFile, ...]

    @classmethod
    def from_release(
        cls, release: "Release", commit: str, dirty: bool = False, path_prefix: str = ""
    ) -> "DeploymentState":
        state = cls._validated(commit, dirty, path_prefix, tuple(release.files))
        state.serialize()
        return state

    @classmethod
    def parse(cls, payload: bytes | str) -> "DeploymentState":
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        if len(payload) > _MAX_DEPLOYMENT_STATE_BYTES:
            raise BodaError("Deployment state exceeds 1 MiB")
        try:
            value = json.loads(
                payload.decode("utf-8"), object_pairs_hook=_strict_json_object
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise BodaError("Invalid deployment state JSON") from exc
        if not isinstance(value, dict) or set(value) != {
            "schema",
            "commit",
            "dirty",
            "path_prefix",
            "files",
        }:
            raise BodaError("Invalid deployment state fields")
        if value["schema"] != _DEPLOYMENT_STATE_SCHEMA or not isinstance(
            value["files"], list
        ):
            raise BodaError("Invalid deployment state schema")
        entries = []
        for item in value["files"]:
            if (
                not isinstance(item, dict)
                or set(item) != {"path", "sha256"}
                or not isinstance(item["path"], str)
                or not isinstance(item["sha256"], str)
            ):
                raise BodaError("Invalid deployment state file entry")
            parsed_path = _release_path(item["path"])
            if parsed_path.as_posix() != item["path"]:
                raise BodaError("Non-canonical deployment state path")
            entries.append(ReleaseFile(parsed_path, item["sha256"]))
        return cls._validated(
            value["commit"], value["dirty"], value["path_prefix"], tuple(entries)
        )

    @classmethod
    def _validated(
        cls,
        commit: object,
        dirty: object,
        path_prefix: object,
        files: tuple[ReleaseFile, ...],
    ) -> "DeploymentState":
        if (
            not isinstance(commit, str)
            or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit)
            or not isinstance(dirty, bool)
            or not isinstance(path_prefix, str)
        ):
            raise BodaError("Invalid deployment state metadata")
        prefix = _path_prefix(path_prefix)
        if prefix != path_prefix:
            raise BodaError("Deployment state path prefix is not canonical")
        seen: set[PurePosixPath] = set()
        for entry in files:
            if (
                not isinstance(entry, ReleaseFile)
                or entry.path == PurePosixPath(".")
                or entry.path in seen
                or entry.path.parts[0] in _RESERVED_DEPLOYMENT_PATHS
                or not re.fullmatch(r"[0-9a-f]{64}", entry.sha256)
            ):
                raise BodaError("Invalid deployment state file manifest")
            seen.add(entry.path)
        digests = {entry.path.as_posix(): entry.sha256 for entry in files}
        if (
            "index.html" not in digests
            or digests.get("index.htm") != digests["index.html"]
        ):
            raise BodaError(
                "Deployment state requires identical index.html and index.htm"
            )
        return cls(commit, dirty, prefix, tuple(sorted(files, key=_deploy_key)))

    def serialize(self) -> bytes:
        value = {
            "schema": _DEPLOYMENT_STATE_SCHEMA,
            "commit": self.commit,
            "dirty": self.dirty,
            "path_prefix": self.path_prefix,
            "files": [
                {"path": e.path.as_posix(), "sha256": e.sha256} for e in self.files
            ],
        }
        encoded = (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        if len(encoded) > _MAX_DEPLOYMENT_STATE_BYTES:
            raise BodaError("Deployment state exceeds 1 MiB")
        return encoded


@dataclass(frozen=True)
class IncrementalPlan:
    uploads: tuple[ReleaseFile, ...]
    deletes: tuple[ReleaseFile, ...]
    unchanged: tuple[ReleaseFile, ...]


@dataclass(frozen=True)
class IncrementalResult:
    uploaded: int
    deleted: int
    unchanged: int


@dataclass(frozen=True)
class UploadReceipt:
    path: PurePosixPath
    public_path: PurePosixPath
    typo_count: int
    review_required: bool
    filesrc: str = field(repr=False)
    typosnoteid: str = field(repr=False)
    security_content: dict[str, object] = field(repr=False)


@dataclass(frozen=True)
class DirectoryListing:
    position: str
    folders: frozenset[str]
    files: frozenset[str]


def _load_build_metadata(path: Path) -> tuple[str | None, bool | None]:
    if not path.exists():
        return None, None
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_size > _MAX_BUILD_METADATA_BYTES
    ):
        raise BodaError("Invalid release build metadata")
    try:
        value = json.loads(path.read_text(), object_pairs_hook=_strict_json_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise BodaError("Invalid release build metadata") from exc
    if (
        not isinstance(value, dict)
        or set(value) != {"schema", "commit", "dirty"}
        or value["schema"] != _BUILD_METADATA_SCHEMA
        or not isinstance(value["commit"], str)
        or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value["commit"])
        or not isinstance(value["dirty"], bool)
    ):
        raise BodaError("Invalid release build metadata")
    return value["commit"], value["dirty"]


@dataclass(frozen=True)
class Release:
    root: Path
    files: tuple[ReleaseFile, ...]
    source_commit: str | None = None
    source_dirty: bool | None = None

    @classmethod
    def load(cls, root: str | Path) -> "Release":
        root = Path(root).resolve()
        manifest = root / "SHA256SUMS"
        build_metadata = root / BUILD_METADATA_FILENAME
        source_commit, source_dirty = _load_build_metadata(build_metadata)
        if not manifest.is_file():
            raise BodaError(f"Missing release manifest: {manifest}")

        entries: list[ReleaseFile] = []
        seen: set[PurePosixPath] = set()
        for number, line in enumerate(manifest.read_text().splitlines(), 1):
            try:
                digest, raw_path = line.split(maxsplit=1)
            except ValueError as exc:
                raise BodaError(f"Invalid SHA256SUMS line {number}") from exc
            path = _release_path(raw_path.removeprefix("./"))
            if (
                path.parts[0] in _RESERVED_DEPLOYMENT_PATHS
                or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or path in seen
            ):
                raise BodaError(f"Invalid SHA256SUMS line {number}")
            seen.add(path)
            entries.append(ReleaseFile(path, digest))

        actual = {
            PurePosixPath(path.relative_to(root).as_posix())
            for path in root.rglob("*")
            if path.is_file() and path not in {manifest, build_metadata}
        }
        if actual != seen:
            raise BodaError("Release files do not match SHA256SUMS")

        for entry in entries:
            path = root / entry.path
            if path.is_symlink() or _sha256(path.read_bytes()) != entry.sha256:
                raise BodaError(f"Checksum mismatch: {entry.path}")

        digests = {entry.path.as_posix(): entry.sha256 for entry in entries}
        if (
            "index.html" not in digests
            or digests.get("index.htm") != digests["index.html"]
        ):
            raise BodaError("Release requires identical index.html and index.htm")

        return cls(
            root,
            tuple(sorted(entries, key=_deploy_key)),
            source_commit,
            source_dirty,
        )

    @property
    def directories(self) -> tuple[PurePosixPath, ...]:
        directories = {PurePosixPath(".")}
        for entry in self.files:
            directories.update(entry.path.parents)
        return tuple(sorted(directories, key=lambda path: (len(path.parts), str(path))))


def login_iaaa(
    *,
    username: str,
    password: str,
    otp_secret: str = "",
    timeout: int = 60,
    session: requests.Session | None = None,
) -> requests.Session:
    """Create a temporary authenticated Boda session through PKU IAAA."""
    username = _credential(username, "BODA_IAAA_USERNAME")
    password = _credential(password, "BODA_IAAA_PASSWORD")
    session = session or requests.Session()
    session.headers.update({"User-Agent": "lmxu-group-boda-release/1"})
    login_url = f"{_IAAA_BASE_URL}/iaaa/oauth.jsp"
    network_action = "IAAA login page"
    try:
        response = session.get(
            login_url,
            params={
                "appID": _IAAA_APP_ID,
                "appName": _IAAA_APP_NAME,
                "redirectUrl": _BODA_CAS_URL,
            },
            allow_redirects=False,
            timeout=timeout,
        )
        _expect_ok(response, "IAAA login page")
        app_id, redirect_url = _parse_iaaa_login_page(response.text)
        login_page_url = response.url if isinstance(response.url, str) else login_url

        network_action = "IAAA public key"
        response = session.get(
            f"{_IAAA_BASE_URL}/iaaa/getPublicKey.do",
            allow_redirects=False,
            timeout=timeout,
        )
        _expect_ok(response, "IAAA public key")
        key_payload = response.json()
        if key_payload.get("success") is not True or not isinstance(
            key_payload.get("key"), str
        ):
            raise BodaError("IAAA public key response is invalid")
        encrypted_password = _encrypt_password(password, key_payload["key"])
        otp_code = _totp_code(otp_secret)

        network_action = "IAAA login"
        response = session.post(
            f"{_IAAA_BASE_URL}/iaaa/oauthlogin.do",
            data={
                "appid": app_id,
                "userName": username,
                "password": encrypted_password,
                "randCode": "",
                "smsCode": "",
                "otpCode": otp_code,
                "remTrustChk": "false",
                "redirUrl": redirect_url,
            },
            headers={
                "Origin": _IAAA_BASE_URL,
                "Referer": login_page_url,
                "X-Requested-With": "XMLHttpRequest",
            },
            allow_redirects=False,
            timeout=timeout,
        )
        _expect_ok(response, "IAAA login")
        result = response.json()
        token = result.get("token")
        if result.get("success") is not True or not isinstance(token, str) or not token:
            raise BodaError(_iaaa_login_failure(result))

        network_action = "Boda CAS handoff"
        response = session.get(
            redirect_url,
            params={"_rand": str(time.time_ns()), "token": token},
            allow_redirects=True,
            timeout=timeout,
        )
        _expect_ok(response, "Boda CAS handoff")
        if not _is_https_host(response.url, "boda.pku.edu.cn") or any(
            not _is_https_host(item.url, "boda.pku.edu.cn") for item in response.history
        ):
            raise BodaError("Boda CAS handoff returned to an unexpected host")

        network_action = "Boda authorization refresh"
        response = session.post(
            "https://boda.pku.edu.cn/system/frame/refreshsiteauth.jsp",
            headers={
                "Origin": "https://boda.pku.edu.cn",
                "Referer": "https://boda.pku.edu.cn/system/frame/changesite.jsp",
                "X-Requested-With": "XMLHttpRequest",
            },
            allow_redirects=False,
            timeout=timeout,
        )
        _expect_ok(response, "Boda authorization refresh")
    except requests.RequestException as exc:
        raise BodaError(
            f"{network_action} network request failed ({type(exc).__name__})"
        ) from exc
    except (AttributeError, TypeError, ValueError) as exc:
        raise BodaError("IAAA login response is invalid") from exc
    return session


def load_persistent_session(path: str | Path) -> requests.Session:
    """Load a private Netscape-format cookie jar into a requests session."""
    path = Path(path)
    if not path.exists():
        try:
            path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        except OSError as exc:
            raise BodaError("Boda session directory could not be created") from exc
    jar = MozillaCookieJar(str(path))
    if path.is_symlink():
        raise BodaError("Boda session file must not be a symlink")
    if path.exists():
        details = path.stat()
        if (
            not path.is_file()
            or details.st_uid != os.getuid()
            or details.st_mode & 0o077
        ):
            raise BodaError("Boda session file must be a private regular file")
        try:
            jar.load(ignore_discard=True, ignore_expires=False)
        except (LoadError, OSError) as exc:
            raise BodaError("Boda session file is invalid") from exc
    session = requests.Session()
    session.cookies = jar
    return session


def save_persistent_session(session: requests.Session) -> None:
    """Save a persistent session without exposing cookie values."""
    jar = session.cookies
    if not isinstance(jar, MozillaCookieJar) or not jar.filename:
        raise BodaError("Boda session is not persistent")
    path = Path(jar.filename)
    if path.is_symlink():
        raise BodaError("Boda session file must not be a symlink")
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        jar.save(str(temporary_path), ignore_discard=True, ignore_expires=False)
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, path)
    except OSError as exc:
        raise BodaError("Boda session file could not be saved") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


class BodaClient:
    """Confirmed Boda file operations using an existing browser session."""

    def __init__(
        self,
        *,
        allowed_root: str | None = None,
        path_prefix: str = "",
        base_url: str = "https://boda.pku.edu.cn",
        public_url: str = "https://xulm.pku.edu.cn",
        timeout: int = 60,
        session: requests.Session | None = None,
    ) -> None:
        _exact_https_host(base_url, "boda.pku.edu.cn")
        _exact_https_host(public_url, "xulm.pku.edu.cn")
        if session is None:
            raise BodaError("Authenticated Boda session is required")
        path_prefix = _path_prefix(path_prefix)
        prefix_root = _root_from_path_prefix(path_prefix)
        if allowed_root and path_prefix and allowed_root != prefix_root:
            raise BodaError("Boda root and public path prefix do not match")
        allowed_root = allowed_root or prefix_root
        if not re.fullmatch(
            r"FOLD:(?:[A-Za-z0-9_-]+(?:\|[A-Za-z0-9_-]+)*)?", allowed_root
        ):
            raise BodaError("Invalid Boda root")

        self.base_url = base_url.rstrip("/")
        self.public_url = public_url.rstrip("/")
        self.path_prefix = path_prefix
        self.allowed_root = allowed_root
        self.timeout = timeout
        self.session = session
        self.session.headers.update({"User-Agent": "lmxu-group-boda-release/1"})

    def list_directory(self, directory: str | PurePosixPath = ".") -> DirectoryListing:
        position = self._position(directory)
        try:
            response = self.session.get(
                f"{self.base_url}/system/site/foldercontent.jsp",
                params={"position": position, "folder_name": ""},
                allow_redirects=False,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise BodaError("Boda directory probe network request failed") from exc
        if "您需要登录后才可访问系统" in response.text:
            raise BodaAuthenticationError("Boda session has expired")
        if response.status_code in {301, 302, 303, 307, 308, 401}:
            raise BodaAuthenticationError("Boda session has expired")
        _expect_ok(response, "directory probe")
        return _parse_listing(response.text, position)

    def upload_file(
        self,
        directory: str | PurePosixPath,
        local_path: Path,
        *,
        overwrite: bool,
    ) -> UploadReceipt | None:
        if not overwrite:
            raise BodaError("Upload requires explicit overwrite approval")
        name = local_path.name
        _release_path(name)
        position = self._position(directory)
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        with local_path.open("rb") as stream:
            response = self.session.post(
                f"{self.base_url}/system/site/newfileajax.jsp",
                params={"position": position, "actiontype": "upload"},
                data={"filename": name, "filedesc": name, "overwrite": "ok"},
                files={"file": (name, stream, mime)},
                headers={
                    "Referer": f"{self.base_url}/system/site/newfilemulit.jsp",
                    "X-Requested-With": "XMLHttpRequest",
                },
                allow_redirects=False,
                timeout=self.timeout,
            )
        _expect_ok(response, f"upload {name}")
        if response.content == b"ok":
            return None
        try:
            payload = response.json()
        except requests.exceptions.JSONDecodeError as exc:
            raise BodaUploadReceiptError(
                f"Boda returned a non-JSON upload receipt for {name}"
            ) from exc
        try:
            if not isinstance(payload, list) or len(payload) != 1:
                raise ValueError("payload is not a single-item list")
            item = payload[0]
            if not isinstance(item, dict):
                raise ValueError("upload item is not an object")
            content = item.get("content") or {}
            filesrc = item.get("filesrc")
            typosnoteid = item.get("typosnoteid")
            if not isinstance(content, dict):
                raise ValueError("security content is not an object")
            if not isinstance(filesrc, str):
                raise ValueError("filesrc is missing")
            if (
                isinstance(typosnoteid, bool)
                or not isinstance(typosnoteid, (int, str))
                or str(typosnoteid) == ""
            ):
                raise ValueError("typosnoteid is missing")
            typo_count = int(content.get("typosnum") or 0)
            public_path = _public_path_from_filesrc(filesrc)
            if public_path != self._expected_public_path(directory, name):
                raise ValueError("public path does not match the upload target")
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
            raise BodaError(f"Unexpected upload response for {name}: {exc}") from exc
        return UploadReceipt(
            PurePosixPath(directory) / name,
            public_path,
            typo_count,
            bool(content.get("hastypos") or typo_count),
            filesrc,
            str(typosnoteid),
            content,
        )

    def update_security_record(self, receipt: UploadReceipt, reason: str) -> None:
        reason = _security_reason(reason)
        response = self.session.get(
            f"{self.base_url}/system/_js/typoscheck/dofiletypos.jsp",
            allow_redirects=False,
            timeout=self.timeout,
        )
        _expect_ok(response, "security form")
        owner, state = _parse_security_page(response.text)
        try:
            sensitive_result = _encode_post_param(
                json.dumps(
                    receipt.security_content,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
            ignore_content = _encode_post_param(
                _build_ignore_content(receipt.security_content)
            )
        except (TypeError, ValueError) as exc:
            raise BodaError("Boda upload security content is incomplete") from exc
        response = self.session.post(
            f"{self.base_url}/system/_js/typoscheck/updatefilesecurityinfo.jsp",
            data={
                "owner": owner,
                "typosnoteid": receipt.typosnoteid,
                "filesrc": receipt.filesrc,
                "wbignorereason": reason,
                "wbsensitiveresult": sensitive_result,
                "ignorecontent": ignore_content,
                "state": state,
            },
            allow_redirects=False,
            timeout=self.timeout,
        )
        _expect_ok(response, "security update")
        if _sha256(response.content) != _SECURITY_UPDATE_RESPONSE_SHA256:
            raise BodaError("Unexpected Boda security-update response")

    def verify_public(
        self,
        entry: ReleaseFile,
        public_path: PurePosixPath | None = None,
    ) -> None:
        public_path = public_path or self._expected_public_path(
            ".", entry.path.as_posix()
        )
        url = f"{self.public_url}/{quote(public_path.as_posix())}"
        last_response: requests.Response | None = None
        last_network_error: requests.RequestException | None = None
        for attempt in range(5):
            try:
                response = requests.get(
                    url,
                    params={
                        "boda_release": entry.sha256[:12],
                        "boda_check": f"{time.time_ns()}-{attempt}",
                    },
                    headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
                    allow_redirects=False,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                last_network_error = exc
            else:
                last_response = response
                if response.status_code == 200:
                    content = response.content
                    if entry.path.suffix.lower() in {".css", ".js"}:
                        content = content.removeprefix(b"\xef\xbb\xbf")
                    if _sha256(content) == entry.sha256:
                        return
            if attempt < 4:
                time.sleep(1)

        if last_response is None:
            raise BodaError(
                f"Public verification network request failed: {entry.path}"
            ) from last_network_error

        _expect_ok(last_response, f"public verification {entry.path}")
        raise BodaError(f"Public checksum mismatch: {entry.path}")

    def verify_public_absent(self, entry: ReleaseFile) -> None:
        public_path = self._expected_public_path(".", entry.path.as_posix())
        url = f"{self.public_url}/{quote(public_path.as_posix())}"
        last_response: requests.Response | None = None
        last_network_error: requests.RequestException | None = None
        consecutive_missing = 0
        for attempt in range(5):
            try:
                response = requests.get(
                    url,
                    params={
                        "boda_delete": entry.sha256[:12],
                        "boda_check": f"{time.time_ns()}-{attempt}",
                    },
                    headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
                    allow_redirects=False,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                last_network_error = exc
            else:
                last_response = response
                if response.status_code == 404:
                    consecutive_missing += 1
                    if consecutive_missing >= 2:
                        return
                else:
                    consecutive_missing = 0
            if attempt < 4:
                time.sleep(1)

        if last_response is None:
            raise BodaError(
                f"Public deletion verification network request failed: {entry.path}"
            ) from last_network_error
        raise BodaError(f"Deleted file is still publicly reachable: {entry.path}")

    def read_deployment_state(self) -> DeploymentState:
        path = self._expected_public_path(".", DEPLOYMENT_STATE_FILENAME)
        url = f"{self.public_url}/{quote(path.as_posix())}"
        last_response: requests.Response | None = None
        last_network_error: requests.RequestException | None = None
        for attempt in range(3):
            try:
                response = requests.get(
                    url,
                    params={
                        "boda_state": hashlib.sha256(
                            f"{time.time_ns()}-{attempt}".encode()
                        ).hexdigest()[:16]
                    },
                    headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
                    allow_redirects=False,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                last_network_error = exc
            else:
                last_response = response
                if response.status_code != 404:
                    break
            if attempt < 2:
                time.sleep(1)

        if last_response is None:
            raise BodaError(
                "Deployment state network request failed"
            ) from last_network_error
        if last_response.status_code == 404:
            raise DeploymentStateNotFound("Deployment state not found")
        if last_response.status_code != 200:
            raise BodaError(
                f"Deployment state fetch failed with HTTP {last_response.status_code}"
            )
        if len(last_response.content) > _MAX_DEPLOYMENT_STATE_BYTES:
            raise BodaError("Deployment state exceeds 1 MiB")
        state = DeploymentState.parse(last_response.content)
        if state.path_prefix != self.path_prefix:
            raise BodaError("Deployment state path prefix does not match client")
        return state

    get_deployment_state = read_deployment_state

    def create_directory(
        self,
        parent: str | PurePosixPath,
        name: str,
        description: str = "",
    ) -> bool:
        name = _entry_name(name)
        before = self.list_directory(parent)
        if name in before.folders:
            return False

        response = self.session.get(
            f"{self.base_url}/system/site/newfolder.jsp",
            params={"position": before.position, "folder_name": ""},
            headers={"Referer": f"{self.base_url}/system/site/foldercontent.jsp"},
            allow_redirects=False,
            timeout=self.timeout,
        )
        _expect_ok(response, "create-directory form")
        form = _parse_newfolder_form(response.text, before.position)
        response = self.session.post(
            f"{self.base_url}/system/site/foldercontent.jsp",
            params={"actiontype": "new_directory"},
            data={
                "CSRF_TOKENKEY": form["CSRF_TOKENKEY"],
                "position": form["position"],
                "folder_name": form["folder_name"],
                "dir_name": name,
                "dir_desc": description or name,
                "ok": _CREATE_DIRECTORY_OK,
            },
            headers={"Referer": f"{self.base_url}/system/site/newfolder.jsp"},
            allow_redirects=False,
            timeout=self.timeout,
        )
        _expect_ok(response, "create directory")
        after = self.list_directory(parent)
        if name not in after.folders:
            raise BodaError(f"Boda did not create directory: {name}")
        return True

    def delete_file(self, directory: str | PurePosixPath, name: str) -> bool:
        return self._delete_entry(directory, _entry_name(name), is_directory=False)

    def delete_directory(self, parent: str | PurePosixPath, name: str) -> bool:
        return self._delete_entry(parent, _entry_name(name), is_directory=True)

    def _delete_entry(
        self,
        directory: str | PurePosixPath,
        name: str,
        *,
        is_directory: bool,
    ) -> bool:
        before = self.list_directory(directory)
        entries = before.folders if is_directory else before.files
        if name not in entries:
            return False
        data = _folder_action_data(before.position)
        data["folder_name" if is_directory else "file_name"] = name
        response = self.session.post(
            f"{self.base_url}/system/site/foldercontent.jsp",
            params={"frame": "fileright"},
            data=data,
            allow_redirects=False,
            timeout=self.timeout,
        )
        _expect_ok(response, "delete directory" if is_directory else "delete file")
        after = self.list_directory(directory)
        remaining = after.folders if is_directory else after.files
        if name in remaining:
            kind = "directory" if is_directory else "file"
            raise BodaError(f"Boda did not delete {kind}: {name}")
        return True

    def _position(self, directory: str | PurePosixPath) -> str:
        path = _release_directory(directory)
        if path == PurePosixPath("."):
            return self.allowed_root
        if self.allowed_root == "FOLD:":
            return f"FOLD:{'|'.join(path.parts)}"
        return f"{self.allowed_root}|{'|'.join(path.parts)}"

    def _expected_public_path(
        self, directory: str | PurePosixPath, name: str
    ) -> PurePosixPath:
        root = self.allowed_root.removeprefix("FOLD:")
        parts = [part for part in root.split("|") if part]
        directory_path = _release_directory(directory)
        if directory_path != PurePosixPath("."):
            parts.extend(directory_path.parts)
        name_path = _release_path(name)
        parts.extend(name_path.parts)
        return PurePosixPath(*parts)


def run_crud_test(client: BodaClient) -> bool:
    """Create and remove a disposable Boda directory and file."""
    if client.allowed_root != "FOLD:test":
        raise BodaError("CRUD test requires Boda root FOLD:test")

    directory_name = "A"
    file_name = "B.txt"
    cleanup_required = False
    upload_receipt_verified = True
    try:
        if directory_name in client.list_directory().folders:
            raise BodaError(
                f"CRUD test refused because directory {directory_name} already exists"
            )
        cleanup_required = True
        if not client.create_directory(".", directory_name):
            cleanup_required = False
            raise BodaError(f"CRUD test could not create directory {directory_name}")
        with tempfile.TemporaryDirectory() as temporary_directory:
            local_path = Path(temporary_directory) / file_name
            local_path.write_text("Boda CRUD smoke test\n")
            try:
                receipt = client.upload_file(directory_name, local_path, overwrite=True)
                if receipt is None:
                    upload_receipt_verified = False
            except BodaUploadReceiptError:
                upload_receipt_verified = False
        if file_name not in client.list_directory(directory_name).files:
            raise BodaError(f"CRUD test could not verify file {file_name}")
        if not client.delete_file(directory_name, file_name):
            raise BodaError(f"CRUD test could not delete file {file_name}")
        if not client.delete_directory(".", directory_name):
            raise BodaError(f"CRUD test could not delete directory {directory_name}")
        cleanup_required = False
    except BaseException as original:
        cleanup_errors: list[str] = []
        if cleanup_required:
            try:
                client.delete_file(directory_name, file_name)
            except BaseException as cleanup_error:
                cleanup_errors.append(f"file cleanup failed: {cleanup_error}")
            try:
                client.delete_directory(".", directory_name)
            except BaseException as cleanup_error:
                cleanup_errors.append(f"directory cleanup failed: {cleanup_error}")
        if cleanup_errors:
            details = "; ".join(cleanup_errors)
            if not isinstance(original, Exception):
                original.add_note(details)
                raise
            raise BodaError(f"{original}; {details}") from original
        if isinstance(original, BodaError):
            raise
        if isinstance(original, Exception):
            raise BodaError(f"CRUD test failed: {original}") from original
        raise
    return upload_receipt_verified


def compute_incremental_plan(
    release: Release, previous: DeploymentState
) -> IncrementalPlan:
    current = {entry.path: entry for entry in release.files}
    old = {entry.path: entry for entry in previous.files}
    for path in old:
        if any(
            PurePosixPath(*path.parts[:depth]) in current
            for depth in range(1, len(path.parts))
        ):
            raise BodaError("Incremental deployment cannot change file/directory shape")
    for path in current:
        if any(
            PurePosixPath(*path.parts[:depth]) in old
            for depth in range(1, len(path.parts))
        ):
            raise BodaError("Incremental deployment cannot change file/directory shape")
    uploads = tuple(
        sorted(
            (
                entry
                for path, entry in current.items()
                if path not in old or old[path].sha256 != entry.sha256
            ),
            key=_deploy_key,
        )
    )
    deletes = tuple(
        sorted(
            (entry for path, entry in old.items() if path not in current),
            key=lambda e: e.path.as_posix(),
        )
    )
    unchanged = tuple(
        sorted(
            (
                entry
                for path, entry in current.items()
                if path in old and old[path].sha256 == entry.sha256
            ),
            key=_deploy_key,
        )
    )
    return IncrementalPlan(uploads, deletes, unchanged)


def publish_deployment_state(
    client: BodaClient, state: DeploymentState, reason: str
) -> None:
    reason = _security_reason(reason)
    content = state.serialize()
    digest = _sha256(content)
    with tempfile.TemporaryDirectory() as temporary_directory:
        local = Path(temporary_directory) / DEPLOYMENT_STATE_FILENAME
        local.write_bytes(content)
        receipt = client.upload_file(".", local, overwrite=True)
        if receipt is not None:
            client.update_security_record(receipt, reason)
        listing = client.list_directory()
        if DEPLOYMENT_STATE_FILENAME not in listing.files:
            raise BodaError("Boda did not create deployment state file")
        client.verify_public(
            ReleaseFile(PurePosixPath(DEPLOYMENT_STATE_FILENAME), digest),
            receipt.public_path if receipt else None,
        )


def deploy_incremental(
    client: BodaClient,
    release: Release,
    previous: DeploymentState,
    commit: str,
    reason: str,
) -> IncrementalResult:
    if previous.dirty:
        raise BodaError("Cannot incrementally deploy from a dirty state")
    reason = _security_reason(reason)
    next_state = DeploymentState.from_release(
        release, commit=commit, dirty=False, path_prefix=client.path_prefix
    )
    if previous.path_prefix != client.path_prefix:
        raise BodaError("Previous deployment state path prefix does not match client")
    plan = compute_incremental_plan(release, previous)
    client.list_directory()
    for entry in previous.files:
        client.verify_public(entry)
    old_paths = {entry.path for entry in previous.files}
    needed_dirs = sorted(
        {
            directory
            for entry in plan.uploads
            for directory in entry.path.parents
            if directory != PurePosixPath(".")
        },
        key=lambda p: (len(p.parts), p.as_posix()),
    )
    available_dirs = {PurePosixPath(".")}
    for directory in needed_dirs:
        parent = directory.parent
        if parent not in available_dirs:
            continue
        listing = client.list_directory(parent)
        if directory.name in listing.files:
            raise BodaError(f"Remote file blocks directory: {directory}")
        if directory.name in listing.folders:
            available_dirs.add(directory)
    for entry in plan.uploads:
        if entry.path.parent not in available_dirs:
            continue
        listing = client.list_directory(entry.path.parent)
        if entry.path.name in listing.folders or (
            entry.path.name in listing.files and entry.path not in old_paths
        ):
            raise BodaError(f"Unmanaged remote entry collision: {entry.path}")
    if client.read_deployment_state() != previous:
        raise BodaError("Deployment state changed during incremental preflight")
    for directory in needed_dirs:
        client.create_directory(
            directory.parent, directory.name, "Hugo release directory"
        )
    for entry in plan.uploads:
        listing = client.list_directory(entry.path.parent)
        if entry.path.name in listing.folders:
            raise BodaError(f"Remote directory blocks file: {entry.path}")
        if entry.path in old_paths:
            if entry.path.name not in listing.files:
                raise BodaError(f"Managed remote file disappeared: {entry.path}")
        elif entry.path.name in listing.files:
            raise BodaError(f"Unmanaged remote entry collision: {entry.path}")
    for entry in plan.uploads:
        receipt = client.upload_file(
            entry.path.parent, release.root / entry.path, overwrite=True
        )
        if receipt is not None:
            client.update_security_record(receipt, reason)
    for entry in plan.uploads:
        client.verify_public(entry)
    for entry in plan.deletes:
        if not client.delete_file(entry.path.parent, entry.path.name):
            raise BodaError(f"Remote deletion drift: {entry.path}")
        client.verify_public_absent(entry)
    if client.read_deployment_state() != previous:
        raise BodaError("Deployment state changed during incremental deployment")
    publish_deployment_state(client, next_state, reason)
    return IncrementalResult(len(plan.uploads), len(plan.deletes), len(plan.unchanged))


def deploy_release(
    client: BodaClient,
    release: Release,
    security_reason: str,
) -> int:
    """Run a non-atomic upload, with both root entry files ordered last."""
    security_reason = _security_reason(security_reason)
    client.list_directory()
    for directory in release.directories:
        if directory != PurePosixPath("."):
            client.create_directory(
                directory.parent,
                directory.name,
                "Hugo release directory",
            )

    verifications: list[tuple[ReleaseFile, PurePosixPath | None]] = []
    for entry in release.files:
        receipt = client.upload_file(
            entry.path.parent,
            release.root / entry.path,
            overwrite=True,
        )
        if receipt is None:
            verifications.append((entry, None))
        else:
            client.update_security_record(receipt, security_reason)
            verifications.append((entry, receipt.public_path))

    for entry, public_path in verifications:
        client.verify_public(entry, public_path)
    return len(verifications)


def _release_path(raw: str) -> PurePosixPath:
    path = PurePosixPath(raw)
    if (
        not raw
        or path.is_absolute()
        or ".." in path.parts
        or any(not re.fullmatch(r"[A-Za-z0-9._-]+", part) for part in path.parts)
    ):
        raise BodaError(f"Unsafe release path: {raw}")
    return path


def _release_directory(raw: str | PurePosixPath) -> PurePosixPath:
    path = PurePosixPath(raw)
    if path == PurePosixPath("."):
        return path
    if (
        path.is_absolute()
        or ".." in path.parts
        or any(not re.fullmatch(r"[A-Za-z0-9_-]+", part) for part in path.parts)
    ):
        raise BodaError(f"Unsafe release directory: {raw}")
    return path


def _entry_name(raw: str) -> str:
    path = _release_path(raw)
    if len(path.parts) != 1:
        raise BodaError(f"Unsafe entry name: {raw}")
    return raw


def _path_prefix(raw: str) -> str:
    if raw in {"", "/"}:
        return ""
    if not re.fullmatch(r"(?:/[A-Za-z0-9_-]+)+/?", raw):
        raise BodaError(f"Unsafe path prefix: {raw}")
    return "/" + "/".join(part for part in raw.split("/") if part)


def _root_from_path_prefix(path_prefix: str) -> str:
    path_prefix = _path_prefix(path_prefix)
    return "FOLD:" + "|".join(path_prefix.removeprefix("/").split("/"))


def _public_path_from_filesrc(filesrc: str) -> PurePosixPath:
    marker = "/_webprj/"
    if marker not in filesrc:
        raise BodaError("Unexpected Boda upload path")
    return _release_path(filesrc.partition(marker)[2])


def _deploy_key(entry: ReleaseFile) -> tuple[int, str]:
    path = entry.path.as_posix()
    if path == "index.htm":
        stage = 3
    elif path == "index.html":
        stage = 2
    elif entry.path.suffix.lower() in {".htm", ".html"}:
        stage = 1
    else:
        stage = 0
    return stage, path


def _exact_https_host(url: str, host: str) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.netloc != host
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise BodaError(f"URL must use https://{host}")


def _is_https_host(url: str, host: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme == "https" and parsed.netloc == host


def _credential(value: str, name: str) -> str:
    if not value or not value.strip() or "\r" in value or "\n" in value:
        raise BodaError(f"{name} is missing or invalid")
    return value


def _iaaa_login_failure(result: object) -> str:
    details: list[str] = []

    def collect(value: object) -> None:
        if isinstance(value, str):
            details.append(value)
        elif isinstance(value, dict):
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(result)
    message = " ".join(details)
    if re.search(r"otp|动态口令|一次性口令|二次验证|短信", message, re.IGNORECASE):
        return "IAAA login requires or rejected secondary verification"
    if re.search(r"captcha|验证码|randcode", message, re.IGNORECASE):
        return "IAAA login requires a captcha"
    if re.search(r"密码|口令|用户名|账号|用户", message, re.IGNORECASE):
        return "IAAA username or password was rejected"
    return "IAAA login failed"


def _parse_iaaa_login_page(content: str) -> tuple[str, str]:
    parser = _InputParser()
    parser.feed(content)
    app_ids = {
        item.get("value") or "" for item in parser.inputs if item.get("id") == "appid"
    }
    redirects = set(
        re.findall(r'redirectURL\s*=\s*["\'](https://[^"\']+)["\']', content)
    )
    if app_ids != {_IAAA_APP_ID} or redirects != {_BODA_CAS_URL}:
        raise BodaError("IAAA login page targets an unexpected application")
    return _IAAA_APP_ID, _BODA_CAS_URL


def _encrypt_password(password: str, public_key: str) -> str:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        key = serialization.load_pem_public_key(public_key.encode())
        encrypted = key.encrypt(password.encode(), padding.PKCS1v15())
    except (AttributeError, ImportError, TypeError, ValueError) as exc:
        raise BodaError("IAAA password encryption failed") from exc
    return base64.b64encode(encrypted).decode()


def _totp_code(secret: str) -> str:
    secret = secret.strip()
    if not secret:
        return ""
    if re.fullmatch(r"\d{6}", secret):
        return secret
    try:
        import pyotp

        if secret.startswith("otpauth://"):
            otp = pyotp.parse_uri(secret)
            if not isinstance(otp, pyotp.TOTP):
                raise ValueError
            return otp.now()
        return pyotp.TOTP(secret).now()
    except (ImportError, TypeError, ValueError, binascii.Error) as exc:
        raise BodaError("BODA_IAAA_OTP is invalid") from exc


class _InputParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "input":
            self.inputs.append(dict(attrs))

    def values(self, name: str) -> list[str]:
        return [
            item.get("value") or "" for item in self.inputs if item.get("name") == name
        ]


def _parse_listing(content: str, expected: str) -> DirectoryListing:
    parser = _InputParser()
    parser.feed(content)
    positions = [
        item.get("value") or ""
        for item in parser.inputs
        if item.get("name") == "position" and item.get("type") == "hidden"
    ]
    if expected not in positions:
        if "iaaa.pku.edu.cn/iaaa/" in content or "/system/caslogin.jsp" in content:
            raise BodaAuthenticationError("Boda session has expired")
        raise BodaError("Boda session or target directory is invalid")
    return DirectoryListing(
        expected,
        frozenset(value for value in parser.values("folder_name") if value),
        frozenset(value for value in parser.values("file_name") if value),
    )


def _parse_newfolder_form(content: str, expected: str) -> dict[str, str]:
    parser = _InputParser()
    parser.feed(content)
    csrf_inputs = [
        item
        for item in parser.inputs
        if item.get("name") == "CSRF_TOKENKEY" and item.get("type") == "hidden"
    ]
    if len(csrf_inputs) != 1 or not csrf_inputs[0].get("value"):
        raise BodaError("Boda create-directory CSRF token is missing")
    position = _single_input(parser, "position", allow_empty=True)
    folder_name = _single_input(parser, "folder_name", allow_empty=True)
    if not _form_position_matches(position, expected):
        raise BodaError("Boda create-directory form targets another directory")
    return {
        "CSRF_TOKENKEY": csrf_inputs[0]["value"] or "",
        "position": position,
        "folder_name": folder_name,
    }


def _single_input(parser: _InputParser, name: str, *, allow_empty: bool) -> str:
    values = parser.values(name)
    if len(values) != 1 or (not allow_empty and not values[0]):
        raise BodaError(f"Boda form field is missing: {name}")
    return values[0]


def _form_position_matches(raw: str, expected: str) -> bool:
    decoded = unquote(raw)
    relative = expected.removeprefix("FOLD:")
    if not relative:
        return decoded in {"", "FOLD:"}
    return decoded in {
        expected,
        relative,
        relative.replace("|", "/"),
    }


def _folder_action_data(position: str) -> dict[str, str]:
    return {
        "actiontype": "file_delete",
        "templatesname": "",
        "frame": "",
        "file_remark": "",
        "sortkey": "name",
        "sortorder": "ascend",
        "position": position,
        "clipboard_path": "",
        "clipboard_file": "",
        "clipboard_action": "",
    }


def _parse_security_page(content: str) -> tuple[str, str]:
    owner = _single_javascript_number(content, "owner")
    state = _single_javascript_number(content, "state")
    return owner, state


def _single_javascript_number(content: str, name: str) -> str:
    values = set(re.findall(rf'["\']{re.escape(name)}["\']\s*:\s*["\']?(\d+)', content))
    if len(values) != 1:
        raise BodaError("Boda security form is incomplete")
    return values.pop()


def _security_reason(reason: str) -> str:
    reason = reason.strip()
    if not reason:
        raise BodaError("BODA_SECURITY_REASON is missing")
    return reason


def _encode_post_param(value: str) -> str:
    characters = list(base64.b64encode(value.encode()).decode()[::-1])
    for index in range(2, len(characters), 2):
        characters[index - 1], characters[index] = (
            characters[index],
            characters[index - 1],
        )
    return "".join(characters)


def _build_ignore_content(content: dict[str, object]) -> str:
    typos = content.get("typos")
    if not isinstance(typos, list):
        raise BodaError("Boda upload security content is incomplete")
    ignored: list[str] = []
    for item in typos:
        if not isinstance(item, dict) or not isinstance(item.get("oldstr"), str):
            raise BodaError("Boda upload security content is incomplete")
        try:
            kind = int(item["types"])
        except (KeyError, TypeError, ValueError) as exc:
            raise BodaError("Boda upload security content is incomplete") from exc
        reason = f"({item['reason']})" if item.get("reason") else ""
        if kind == 1:
            type_text, message = f"敏感词{reason}", "建议更换为"
        elif kind == 2:
            type_text, message = f"敏感人物{reason}", "建议删除"
        elif kind == 3:
            type_text, message = "错别字", "建议更换为"
        elif kind == 4:
            type_text, message = f"疑似非法链接{reason}", "建议删除"
        elif kind == 5:
            type_text, message = "疑似外链", "建议删除"
        elif kind >= 6:
            type_text, message = "疑似隐私信息", "建议删除"
        else:
            raise BodaError("Boda upload security content is incomplete")
        ignored.append(
            json.dumps(
                {
                    "文件内容": {
                        "typeStr": type_text,
                        "old": f"“{item['oldstr']}”",
                        "msg": message,
                        "new": "",
                    }
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    return "".join(f"~{value}" for value in ignored)


def _expect_ok(response: requests.Response, action: str) -> None:
    if response.status_code != 200:
        raise BodaError(f"Boda {action} failed with HTTP {response.status_code}")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
