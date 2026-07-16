import hashlib
import html
import importlib.util
import json
import os
import stat
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from unittest.mock import Mock, patch

import requests
from requests.cookies import create_cookie

from boda_release import (
    BodaAuthenticationError,
    BodaClient,
    BodaError,
    BodaUploadReceiptError,
    DeploymentState,
    DeploymentStateNotFound,
    DirectoryListing,
    IncrementalResult,
    Release,
    ReleaseFile,
    UploadReceipt,
    compute_incremental_plan,
    deploy_incremental,
    publish_deployment_state,
    _build_ignore_content,
    _encode_post_param,
    _release_path,
    _totp_code,
    deploy_release,
    load_persistent_session,
    login_iaaa,
    run_crud_test,
    save_persistent_session,
)
from boda_release.__main__ import (
    GitSnapshot,
    _client,
    _default_security_reason,
    _default_session_path,
    _env,
    _git_snapshot,
    _release_snapshot,
    main as cli_main,
)


def _response(*, text="", content=None, payload=None, status=200):
    response = Mock(
        status_code=status,
        text=text,
        content=text.encode() if content is None else content,
    )
    if payload is not None:
        response.json.return_value = payload
    return response


def _listing(position, *, folders=(), files=()):
    inputs = [f'<input type="hidden" name="position" value="{html.escape(position)}">']
    inputs.extend(
        f'<input name="folder_name" value="{html.escape(name)}">' for name in folders
    )
    inputs.extend(
        f'<input name="file_name" value="{html.escape(name)}">' for name in files
    )
    return "".join(inputs)


def _receipt(content=None):
    content = content or {"typos": [], "typosnum": 0, "hastypos": False}
    return UploadReceipt(
        PurePosixPath("index.html"),
        PurePosixPath("new/index.html"),
        int(content.get("typosnum", 0)),
        bool(content.get("hastypos")),
        "/system/_owners/example/_webprj/new/index.html",
        "12345",
        content,
    )


def _release_fixture(
    *extra: ReleaseFile,
    source_commit: str = "b" * 40,
    source_dirty: bool = False,
) -> Release:
    files = (
        ReleaseFile(PurePosixPath("index.html"), "a" * 64),
        ReleaseFile(PurePosixPath("index.htm"), "a" * 64),
        *extra,
    )
    return Release(Path("/release"), files, source_commit, source_dirty)


def _iaaa_login_page():
    return (
        '<input type="hidden" id="appid" value="bdwzqnews2025">'
        "<script>redirectURL = "
        '"https://boda.pku.edu.cn/system/caslogin.jsp";</script>'
    )


class ReleaseTest(unittest.TestCase):
    def test_manifest_is_verified_and_root_index_is_last(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                "index.htm": b"home",
                "index.html": b"home",
                "css/site.css": b"css",
                "zh/index.html": b"zh",
            }
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            (root / "SHA256SUMS").write_text(
                "".join(
                    f"{hashlib.sha256(content).hexdigest()}  ./{name}\n"
                    for name, content in files.items()
                )
            )

            release = Release.load(root)

            self.assertEqual(release.files[0].path.as_posix(), "css/site.css")
            self.assertEqual(release.files[-1].path.as_posix(), "index.htm")
            self.assertEqual(
                [str(path) for path in release.directories],
                [".", "css", "zh"],
            )

    def test_release_loads_git_build_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {"index.html": b"home", "index.htm": b"home"}
            for name, content in files.items():
                (root / name).write_bytes(content)
            (root / "BODACLI_BUILD.json").write_text(
                json.dumps({"schema": 1, "commit": "b" * 40, "dirty": False})
            )
            (root / "SHA256SUMS").write_text(
                "".join(
                    f"{hashlib.sha256(content).hexdigest()}  ./{name}\n"
                    for name, content in files.items()
                )
            )

            release = Release.load(root)

            self.assertEqual(release.source_commit, "b" * 40)
            self.assertFalse(release.source_dirty)

    def test_unsafe_path_is_rejected(self):
        with self.assertRaises(BodaError):
            _release_path("../secret")

    @patch("boda_release._totp_code", return_value="123456")
    @patch("boda_release._encrypt_password", return_value="encrypted-password")
    def test_iaaa_login_supports_totp(self, encrypt, totp):
        session = requests.Session()
        handoff = _response()
        handoff.url = "https://boda.pku.edu.cn/system/index.jsp"
        handoff.history = []
        session.get = Mock(
            side_effect=[
                _response(text=_iaaa_login_page()),
                _response(payload={"success": True, "key": "public-key"}),
                handoff,
            ]
        )
        session.post = Mock(
            side_effect=[
                _response(payload={"success": True, "token": "one-time-token"}),
                _response(),
            ]
        )

        result = login_iaaa(
            username="test-user",
            password="test-password",
            otp_secret="BASE32-SECRET",
            session=session,
        )

        self.assertIs(result, session)
        encrypt.assert_called_once_with("test-password", "public-key")
        login_request = session.post.call_args_list[0]
        self.assertEqual(login_request.kwargs["data"]["password"], "encrypted-password")
        self.assertNotEqual(login_request.kwargs["data"]["password"], "test-password")
        self.assertEqual(login_request.kwargs["data"]["otpCode"], "123456")
        self.assertEqual(login_request.kwargs["data"]["remTrustChk"], "false")
        totp.assert_called_once_with("BASE32-SECRET")
        self.assertEqual(
            session.get.call_args_list[2].kwargs["params"]["token"],
            "one-time-token",
        )
        self.assertTrue(
            session.post.call_args_list[1].args[0].endswith("refreshsiteauth.jsp")
        )

    def test_iaaa_login_rejects_missing_credentials_before_network(self):
        session = requests.Session()
        session.get = Mock()

        with self.assertRaises(BodaError):
            login_iaaa(username="", password="test-password", session=session)
        session.get.assert_not_called()

    @patch("boda_release._encrypt_password", return_value="encrypted-password")
    def test_iaaa_login_failure_hides_credentials(self, _):
        session = requests.Session()
        session.get = Mock(
            side_effect=[
                _response(text=_iaaa_login_page()),
                _response(payload={"success": True, "key": "public-key"}),
            ]
        )
        session.post = Mock(
            return_value=_response(
                payload={"success": False, "errors": {"msg": "server detail"}}
            )
        )

        with self.assertRaises(BodaError) as raised:
            login_iaaa(
                username="USER_SECRET",
                password="PASSWORD_SECRET",
                session=session,
            )
        message = str(raised.exception)
        self.assertNotIn("USER_SECRET", message)
        self.assertNotIn("PASSWORD_SECRET", message)
        self.assertNotIn("server detail", message)

    @patch("boda_release._encrypt_password", return_value="encrypted-password")
    def test_iaaa_login_reports_secondary_verification_requirement(self, _):
        session = requests.Session()
        session.get = Mock(
            side_effect=[
                _response(text=_iaaa_login_page()),
                _response(payload={"success": True, "key": "public-key"}),
            ]
        )
        session.post = Mock(
            return_value=_response(
                payload={"success": False, "errors": {"msg": "动态口令错误"}}
            )
        )

        with self.assertRaises(BodaError) as raised:
            login_iaaa(
                username="test-user",
                password="test-password",
                session=session,
            )

        self.assertEqual(
            str(raised.exception),
            "IAAA login requires or rejected secondary verification",
        )

    @patch("boda_release._encrypt_password", return_value="encrypted-password")
    def test_iaaa_login_rejects_handoff_back_to_iaaa(self, _):
        session = requests.Session()
        handoff = _response()
        handoff.url = "https://iaaa.pku.edu.cn/iaaa/oauth.jsp"
        handoff.history = []
        session.get = Mock(
            side_effect=[
                _response(text=_iaaa_login_page()),
                _response(payload={"success": True, "key": "public-key"}),
                handoff,
            ]
        )
        session.post = Mock(
            return_value=_response(payload={"success": True, "token": "one-time-token"})
        )

        with self.assertRaises(BodaError):
            login_iaaa(
                username="test-user",
                password="test-password",
                session=session,
            )

    def test_iaaa_network_errors_are_sanitized(self):
        session = requests.Session()
        session.get = Mock(side_effect=requests.ConnectionError("network detail"))

        with self.assertRaises(BodaError) as raised:
            login_iaaa(
                username="USER_SECRET",
                password="PASSWORD_SECRET",
                session=session,
            )
        self.assertEqual(str(raised.exception), "IAAA/Boda network request failed")

    def test_boda_client_requires_authenticated_session(self):
        with self.assertRaises(BodaError):
            BodaClient()

    def test_persistent_session_round_trip_is_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.cookies"
            session = load_persistent_session(path)
            session.cookies.set_cookie(
                create_cookie(
                    "SESSION",
                    "COOKIE_SECRET",
                    domain="boda.pku.edu.cn",
                    path="/",
                )
            )

            save_persistent_session(session)
            loaded = load_persistent_session(path)

            self.assertEqual(next(iter(loaded.cookies)).value, "COOKIE_SECRET")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_default_session_path_uses_platform_and_xdg_rules(self):
        home = Path("/home/test-user")
        self.assertEqual(
            _default_session_path("darwin", home),
            home / "Library/Caches/bodacli/session.cookies",
        )
        self.assertEqual(
            _default_session_path("linux", home),
            home / ".cache/bodacli/session.cookies",
        )
        self.assertEqual(
            _default_session_path("darwin", home, "/tmp/cache"),
            Path("/tmp/cache/bodacli/session.cookies"),
        )

    def test_missing_session_parent_is_created_private(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory) / "nested" / "cache"
            load_persistent_session(parent / "session.cookies")
            self.assertEqual(stat.S_IMODE(parent.stat().st_mode), 0o700)

    def test_default_security_reason_is_utc_second_precision(self):
        self.assertEqual(
            _default_security_reason(
                datetime(2026, 7, 16, 12, 34, 56, 789000, timezone.utc)
            ),
            "Published by bodacli at 2026-07-16T12:34:56Z.",
        )

    def test_persistent_session_rejects_unsafe_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.cookies"
            path.write_text("# Netscape HTTP Cookie File\n")
            path.chmod(0o644)

            with self.assertRaises(BodaError):
                load_persistent_session(path)

    def test_persistent_session_rejects_broken_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.cookies"
            path.symlink_to(Path(directory) / "missing")

            with self.assertRaises(BodaError):
                load_persistent_session(path)

    @patch("boda_release.__main__._env", return_value="")
    @patch("boda_release.__main__.load_persistent_session")
    @patch("boda_release.__main__.BodaClient")
    def test_client_uses_default_cache_path(self, client_class, load_session, env):
        session = requests.Session()
        session.cookies.set("SESSION", "existing")
        load_session.return_value = session

        _client(
            Namespace(
                path_prefix="/new",
                base_url="https://boda.pku.edu.cn",
                public_url="https://xulm.pku.edu.cn",
            )
        )

        load_session.assert_called_once_with(_default_session_path())

    @patch("boda_release.__main__.save_persistent_session")
    @patch("boda_release.__main__.login_iaaa")
    @patch("boda_release.__main__.BodaClient")
    @patch("boda_release.__main__.load_persistent_session")
    def test_client_reuses_valid_persistent_session(
        self, load_session, client_class, login, save_session
    ):
        session = requests.Session()
        session.cookies.set("SESSION", "existing")
        load_session.return_value = session
        client = client_class.return_value

        result = _client(
            Namespace(
                path_prefix="/new",
                base_url="https://boda.pku.edu.cn",
                public_url="https://xulm.pku.edu.cn",
            )
        )

        self.assertIs(result, client)
        client.list_directory.assert_called_once_with()
        login.assert_not_called()
        save_session.assert_not_called()

    @patch("boda_release.__main__._env")
    @patch("boda_release.__main__.save_persistent_session")
    @patch("boda_release.__main__.login_iaaa")
    @patch("boda_release.__main__.BodaClient")
    @patch("boda_release.__main__.load_persistent_session")
    def test_client_logs_in_with_totp_when_session_is_empty(
        self, load_session, client_class, login, save_session, env
    ):
        session = requests.Session()
        load_session.return_value = session
        env.side_effect = lambda name: {
            "BODA_SESSION_FILE": "",
            "BODA_IAAA_USERNAME": "test-user",
            "BODA_IAAA_PASSWORD": "test-password",
            "BODA_IAAA_OTP": "BASE32-SECRET",
        }.get(name, "")

        _client(
            Namespace(
                path_prefix="/new",
                base_url="https://boda.pku.edu.cn",
                public_url="https://xulm.pku.edu.cn",
            )
        )

        login.assert_called_once_with(
            username="test-user",
            password="test-password",
            otp_secret="BASE32-SECRET",
            session=session,
        )
        client_class.return_value.list_directory.assert_called_once_with()
        save_session.assert_called_once_with(session)

    @patch("boda_release.__main__._env", return_value="test-secret")
    @patch("boda_release.__main__.save_persistent_session")
    @patch("boda_release.__main__.login_iaaa")
    @patch("boda_release.__main__.BodaClient")
    @patch("boda_release.__main__.load_persistent_session")
    def test_client_reauthenticates_only_for_expired_session(
        self, load_session, client_class, login, save_session, _env
    ):
        session = requests.Session()
        session.cookies.set("SESSION", "expired")
        load_session.return_value = session
        client_class.return_value.list_directory.side_effect = [
            BodaAuthenticationError("expired"),
            None,
        ]

        _client(
            Namespace(
                path_prefix="/new",
                base_url="https://boda.pku.edu.cn",
                public_url="https://xulm.pku.edu.cn",
            )
        )

        login.assert_called_once()
        save_session.assert_called_once_with(session)

    @patch("boda_release.__main__.save_persistent_session")
    @patch("boda_release.__main__.login_iaaa")
    @patch("boda_release.__main__.BodaClient")
    @patch("boda_release.__main__.load_persistent_session")
    def test_client_does_not_reauthenticate_on_probe_error(
        self, load_session, client_class, login, save_session
    ):
        session = requests.Session()
        session.cookies.set("SESSION", "existing")
        load_session.return_value = session
        client_class.return_value.list_directory.side_effect = BodaError("probe failed")

        with self.assertRaises(BodaError):
            _client(
                Namespace(
                    path_prefix="/new",
                    base_url="https://boda.pku.edu.cn",
                    public_url="https://xulm.pku.edu.cn",
                )
            )

        login.assert_not_called()
        save_session.assert_not_called()

    def test_cli_reads_local_dotenv_without_logging_values(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text('BODA_IAAA_USERNAME = "test-user"\n')
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("boda_release.__main__.Path", return_value=path),
            ):
                self.assertEqual(_env("BODA_IAAA_USERNAME"), "test-user")

    @patch("boda_release.__main__.publish_deployment_state")
    @patch(
        "boda_release.__main__._git_snapshot",
        return_value=GitSnapshot("b" * 40, False),
    )
    @patch("boda_release.__main__.deploy_release", return_value=1)
    @patch("boda_release.__main__.Release.load")
    @patch("boda_release.__main__._client")
    @patch("boda_release.__main__._env", return_value="explicit reason")
    def test_cli_explicit_security_reason_wins(
        self, env, client, load, deploy, git_snapshot, publish
    ):
        load.return_value = _release_fixture()
        client.return_value.path_prefix = "/new"
        with patch(
            "sys.argv",
            [
                "boda_release",
                "deploy",
                "release",
                "--apply",
                "--confirm",
                "DEPLOY_NONATOMIC",
            ],
        ):
            self.assertEqual(cli_main(), 0)
        deploy.assert_called_once_with(
            client.return_value, load.return_value, "explicit reason"
        )
        published_state = publish.call_args.args[1]
        self.assertEqual(published_state.commit, "b" * 40)
        self.assertFalse(published_state.dirty)

    @patch("boda_release.__main__.publish_deployment_state")
    @patch(
        "boda_release.__main__._git_snapshot",
        return_value=GitSnapshot("b" * 40, True),
    )
    @patch("boda_release.__main__.deploy_release", return_value=1)
    @patch("boda_release.__main__.Release.load")
    @patch("boda_release.__main__._client")
    @patch(
        "boda_release.__main__._default_security_reason", return_value="default reason"
    )
    @patch("boda_release.__main__._env", return_value="")
    def test_cli_full_deploy_refuses_dirty_worktree(
        self, env, reason, client, load, deploy, git_snapshot, publish
    ):
        load.return_value = _release_fixture(source_dirty=True)
        client.return_value.path_prefix = ""
        with patch(
            "sys.argv",
            [
                "boda_release",
                "deploy",
                "release",
                "--apply",
                "--confirm",
                "DEPLOY_NONATOMIC",
            ],
        ):
            self.assertEqual(cli_main(), 1)
        deploy.assert_not_called()
        publish.assert_not_called()

    @patch("boda_release.__main__.deploy_incremental")
    @patch("boda_release.__main__._client")
    def test_cli_incremental_requires_separate_confirmation(self, client, deploy):
        with patch(
            "sys.argv",
            [
                "boda_release",
                "deploy",
                "release",
                "--incremental",
                "--apply",
                "--confirm",
                "DEPLOY_NONATOMIC",
            ],
        ):
            self.assertEqual(cli_main(), 1)
        client.assert_not_called()
        deploy.assert_not_called()

    @patch("boda_release.__main__._git_snapshot")
    @patch(
        "boda_release.__main__.deploy_incremental",
        return_value=IncrementalResult(2, 1, 5),
    )
    @patch("boda_release.__main__.Release.load")
    @patch("boda_release.__main__._client")
    @patch("boda_release.__main__._env", return_value="reason")
    def test_cli_incremental_uses_remote_commit(
        self, env, client, load, deploy, git_snapshot
    ):
        load.return_value = _release_fixture()
        previous = DeploymentState.from_release(
            _release_fixture(), "a" * 40, path_prefix="/new"
        )
        client.return_value.path_prefix = "/new"
        client.return_value.read_deployment_state.return_value = previous
        git_snapshot.return_value = GitSnapshot(
            "b" * 40, False, ("M\tsite/content/en/_index.md",)
        )
        with patch(
            "sys.argv",
            [
                "boda_release",
                "deploy",
                "release",
                "--incremental",
                "--apply",
                "--confirm",
                "DEPLOY_INCREMENTAL",
                "--path-prefix",
                "/new",
            ],
        ):
            self.assertEqual(cli_main(), 0)
        git_snapshot.assert_called_once_with("a" * 40)
        deploy.assert_called_once_with(
            client.return_value,
            load.return_value,
            previous,
            "b" * 40,
            "reason",
        )

    @patch("boda_release.__main__.publish_deployment_state")
    @patch("boda_release.__main__.deploy_release", return_value=3)
    @patch(
        "boda_release.__main__._git_snapshot",
        return_value=GitSnapshot("b" * 40, False),
    )
    @patch("boda_release.__main__.Release.load")
    @patch("boda_release.__main__._client")
    @patch("boda_release.__main__._env", return_value="reason")
    def test_cli_incremental_bootstraps_missing_state(
        self, env, client, load, git_snapshot, deploy, publish
    ):
        load.return_value = _release_fixture()
        client.return_value.path_prefix = "/new"
        client.return_value.list_directory.return_value = DirectoryListing(
            "FOLD:new", frozenset(), frozenset()
        )
        client.return_value.read_deployment_state.side_effect = DeploymentStateNotFound(
            "missing"
        )
        with patch(
            "sys.argv",
            [
                "boda_release",
                "deploy",
                "release",
                "--incremental",
                "--apply",
                "--confirm",
                "DEPLOY_INCREMENTAL",
                "--path-prefix",
                "/new",
            ],
        ):
            self.assertEqual(cli_main(), 0)
        deploy.assert_called_once_with(client.return_value, load.return_value, "reason")
        self.assertFalse(publish.call_args.args[1].dirty)

    @patch("boda_release.__main__.publish_deployment_state")
    @patch("boda_release.__main__.deploy_release")
    @patch(
        "boda_release.__main__._git_snapshot",
        return_value=GitSnapshot("b" * 40, True),
    )
    @patch("boda_release.__main__.Release.load", return_value=_release_fixture())
    @patch("boda_release.__main__._client")
    @patch("boda_release.__main__._env", return_value="reason")
    def test_cli_incremental_refuses_dirty_bootstrap(
        self, env, client, load, git_snapshot, deploy, publish
    ):
        client.return_value.path_prefix = "/new"
        client.return_value.list_directory.return_value = DirectoryListing(
            "FOLD:new", frozenset(), frozenset()
        )
        client.return_value.read_deployment_state.side_effect = DeploymentStateNotFound(
            "missing"
        )
        with patch(
            "sys.argv",
            [
                "boda_release",
                "deploy",
                "release",
                "--incremental",
                "--apply",
                "--confirm",
                "DEPLOY_INCREMENTAL",
                "--path-prefix",
                "/new",
            ],
        ):
            self.assertEqual(cli_main(), 1)
        deploy.assert_not_called()
        publish.assert_not_called()

    @patch("boda_release.__main__.publish_deployment_state")
    @patch("boda_release.__main__.deploy_release")
    @patch("boda_release.__main__._git_snapshot")
    @patch("boda_release.__main__.Release.load", return_value=_release_fixture())
    @patch("boda_release.__main__._client")
    @patch("boda_release.__main__._env", return_value="reason")
    def test_cli_bootstrap_refuses_nonpublic_managed_state(
        self, env, client, load, git_snapshot, deploy, publish
    ):
        client.return_value.path_prefix = "/new"
        client.return_value.read_deployment_state.side_effect = DeploymentStateNotFound(
            "missing"
        )
        client.return_value.list_directory.return_value = DirectoryListing(
            "FOLD:new", frozenset(), frozenset({"bodacli-state.txt"})
        )
        with patch(
            "sys.argv",
            [
                "boda_release",
                "deploy",
                "release",
                "--incremental",
                "--apply",
                "--confirm",
                "DEPLOY_INCREMENTAL",
                "--path-prefix",
                "/new",
            ],
        ):
            self.assertEqual(cli_main(), 1)
        git_snapshot.assert_not_called()
        deploy.assert_not_called()
        publish.assert_not_called()

    def test_upload_request_and_public_path_are_verified(self):
        session = requests.Session()
        response = _response(
            payload=[
                {
                    "filesrc": "/system/_owners/example/_webprj/new/zh/index.html",
                    "typosnoteid": 1,
                    "content": {"hastypos": True, "typosnum": 1, "typos": []},
                }
            ]
        )
        session.post = Mock(return_value=response)
        client = BodaClient(
            allowed_root="FOLD:new",
            session=session,
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text("test")
            receipt = client.upload_file("zh", path, overwrite=True)

        self.assertEqual(receipt.public_path, PurePosixPath("new/zh/index.html"))
        self.assertTrue(receipt.review_required)
        request = session.post.call_args
        self.assertEqual(request.kwargs["params"]["actiontype"], "upload")
        self.assertEqual(request.kwargs["data"]["overwrite"], "ok")
        self.assertEqual(request.kwargs["data"]["filename"], path.name)
        self.assertEqual(request.kwargs["data"]["filedesc"], path.name)
        self.assertEqual(request.kwargs["files"]["file"][0], path.name)
        self.assertIn("file", request.kwargs["files"])

    def test_upload_ok_response_returns_no_receipt(self):
        session = requests.Session()
        session.post = Mock(return_value=_response(text="ok"))
        client = BodaClient(allowed_root="FOLD:new", session=session)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text("test")
            self.assertIsNone(client.upload_file(".", path, overwrite=True))

    def test_upload_ok_with_whitespace_is_not_accepted(self):
        session = requests.Session()
        response = _response(text="ok\n")
        response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value", response.text, 0
        )
        session.post = Mock(return_value=response)
        client = BodaClient(allowed_root="FOLD:new", session=session)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text("test")
            with self.assertRaises(BodaUploadReceiptError):
                client.upload_file(".", path, overwrite=True)

    def test_upload_non_json_response_uses_receipt_error(self):
        session = requests.Session()
        response = _response(text="upload complete")
        response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Expecting value", response.text, 0
        )
        session.post = Mock(return_value=response)
        client = BodaClient(allowed_root="FOLD:test", session=session)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "B.txt"
            path.write_text("test")
            with self.assertRaises(BodaUploadReceiptError):
                client.upload_file("A", path, overwrite=True)

    def test_session_probe_requires_hidden_position(self):
        session = requests.Session()
        response = _response(text=_listing("FOLD:new"))
        session.get = Mock(return_value=response)
        client = BodaClient(
            allowed_root="FOLD:new",
            session=session,
        )

        client.list_directory()

        response.text = "FOLD:new"
        with self.assertRaises(BodaError):
            client.list_directory()

    def test_session_probe_does_not_treat_forbidden_as_expired(self):
        session = requests.Session()
        session.get = Mock(return_value=_response(status=403))
        client = BodaClient(allowed_root="FOLD:new", session=session)

        with self.assertRaises(BodaError) as raised:
            client.list_directory()

        self.assertNotIsInstance(raised.exception, BodaAuthenticationError)

    @unittest.skipUnless(importlib.util.find_spec("pyotp"), "pyotp not installed")
    def test_totp_accepts_base32_and_rejects_invalid_secret(self):
        self.assertEqual(_totp_code("123456"), "123456")
        uri_code = _totp_code(
            "otpauth://totp/Example:test?secret=JBSWY3DPEHPK3PXP&issuer=Example"
        )

        self.assertEqual(len(uri_code), 6)
        self.assertTrue(uri_code.isdigit())
        code = _totp_code("JBSWY3DPEHPK3PXP")
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())
        with self.assertRaises(BodaError):
            _totp_code("not base32!")

    def test_session_probe_treats_login_prompt_as_expired(self):
        session = requests.Session()
        session.get = Mock(return_value=_response(text="您需要登录后才可访问系统"))
        client = BodaClient(allowed_root="FOLD:new", session=session)

        with self.assertRaises(BodaAuthenticationError):
            client.list_directory()

    @patch("boda_release.requests.get")
    def test_path_prefix_controls_root_and_public_verification(self, get):
        content = b"home"
        get.return_value = _response(content=content)
        client = BodaClient(
            path_prefix="/trial/site/",
            session=requests.Session(),
        )
        entry = ReleaseFile(
            PurePosixPath("index.html"), hashlib.sha256(content).hexdigest()
        )

        client.verify_public(entry)

        self.assertEqual(client.path_prefix, "/trial/site")
        self.assertEqual(client.allowed_root, "FOLD:trial|site")
        self.assertEqual(
            get.call_args.args[0],
            "https://xulm.pku.edu.cn/trial/site/index.html",
        )

    @patch("boda_release.time.sleep")
    @patch("boda_release.requests.get")
    def test_public_verification_retries_transient_404(self, get, sleep):
        content = b"home"
        get.side_effect = [
            _response(status=404),
            _response(content=content),
        ]
        client = BodaClient(path_prefix="/new", session=requests.Session())
        entry = ReleaseFile(
            PurePosixPath("index.html"), hashlib.sha256(content).hexdigest()
        )

        client.verify_public(entry)

        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(1)
        first, second = get.call_args_list
        self.assertNotEqual(
            first.kwargs["params"]["boda_check"],
            second.kwargs["params"]["boda_check"],
        )
        self.assertEqual(first.kwargs["headers"]["Cache-Control"], "no-cache")

    def test_unsafe_path_prefix_is_rejected(self):
        with self.assertRaises(BodaError):
            BodaClient(path_prefix="../new", session=requests.Session())

    def test_create_directory_uses_dynamic_csrf_and_verifies_listing(self):
        session = requests.Session()
        session.get = Mock(
            side_effect=[
                _response(text=_listing("FOLD:")),
                _response(
                    text=(
                        '<input type="hidden" name="CSRF_TOKENKEY" '
                        'value="dynamic-token">'
                        '<input type="hidden" name="position" value="">'
                        '<input type="hidden" name="folder_name" value="">'
                    )
                ),
                _response(text=_listing("FOLD:", folders=("test",))),
            ]
        )
        session.post = Mock(return_value=_response())
        client = BodaClient(session=session)

        self.assertTrue(client.create_directory(".", "test", "probe"))
        form_request = session.get.call_args_list[1]
        self.assertEqual(
            form_request.kwargs["params"],
            {"position": "FOLD:", "folder_name": ""},
        )

        request = session.post.call_args
        self.assertEqual(request.kwargs["params"], {"actiontype": "new_directory"})
        self.assertEqual(
            request.kwargs["data"],
            {
                "CSRF_TOKENKEY": "dynamic-token",
                "position": "",
                "folder_name": "",
                "dir_name": "test",
                "dir_desc": "probe",
                "ok": "%E7%A1%AE%E5%AE%9A",
            },
        )

    def test_create_directory_is_idempotent(self):
        session = requests.Session()
        session.get = Mock(
            return_value=_response(text=_listing("FOLD:", folders=("test",)))
        )
        session.post = Mock()
        client = BodaClient(session=session)

        self.assertFalse(client.create_directory(".", "test"))
        session.post.assert_not_called()

    def test_create_directory_requires_post_listing_confirmation(self):
        session = requests.Session()
        session.get = Mock(
            side_effect=[
                _response(text=_listing("FOLD:")),
                _response(
                    text=(
                        '<input type="hidden" name="CSRF_TOKENKEY" value="token">'
                        '<input type="hidden" name="position" value="">'
                        '<input type="hidden" name="folder_name" value="">'
                    )
                ),
                _response(text=_listing("FOLD:")),
            ]
        )
        session.post = Mock(return_value=_response())
        client = BodaClient(session=session)

        with self.assertRaises(BodaError):
            client.create_directory(".", "test")

    def test_delete_file_and_directory_verify_disappearance(self):
        file_session = requests.Session()
        file_session.get = Mock(
            side_effect=[
                _response(text=_listing("FOLD:new", files=("404.html",))),
                _response(text=_listing("FOLD:new")),
            ]
        )
        file_session.post = Mock(return_value=_response())
        file_client = BodaClient(
            allowed_root="FOLD:new",
            session=file_session,
        )

        self.assertTrue(file_client.delete_file(".", "404.html"))
        file_data = file_session.post.call_args.kwargs["data"]
        self.assertEqual(
            file_data,
            {
                "actiontype": "file_delete",
                "templatesname": "",
                "frame": "",
                "file_remark": "",
                "sortkey": "name",
                "sortorder": "ascend",
                "position": "FOLD:new",
                "clipboard_path": "",
                "clipboard_file": "",
                "clipboard_action": "",
                "file_name": "404.html",
            },
        )

        folder_session = requests.Session()
        folder_session.get = Mock(
            side_effect=[
                _response(text=_listing("FOLD:", folders=("probe",))),
                _response(text=_listing("FOLD:")),
            ]
        )
        folder_session.post = Mock(return_value=_response())
        folder_client = BodaClient(session=folder_session)

        self.assertTrue(folder_client.delete_directory(".", "probe"))
        folder_data = folder_session.post.call_args.kwargs["data"]
        self.assertEqual(folder_data["position"], "FOLD:")
        self.assertEqual(folder_data["folder_name"], "probe")
        self.assertEqual(
            folder_session.post.call_args.kwargs["params"],
            {"frame": "fileright"},
        )

    def test_delete_fails_if_target_remains_in_listing(self):
        session = requests.Session()
        listing = _response(text=_listing("FOLD:new", files=("404.html",)))
        session.get = Mock(return_value=listing)
        session.post = Mock(return_value=listing)
        client = BodaClient(
            allowed_root="FOLD:new",
            session=session,
        )

        with self.assertRaises(BodaError):
            client.delete_file(".", "404.html")

    def test_create_directory_rejects_missing_csrf(self):
        session = requests.Session()
        session.get = Mock(
            side_effect=[
                _response(text=_listing("FOLD:")),
                _response(
                    text=(
                        '<input type="hidden" name="position" value="">'
                        '<input type="hidden" name="folder_name" value="">'
                    )
                ),
            ]
        )
        session.post = Mock()
        client = BodaClient(session=session)

        with self.assertRaises(BodaError):
            client.create_directory(".", "test")
        session.post.assert_not_called()

    def test_security_update_requires_reason_and_dynamic_page_fields(self):
        content = {
            "typos": [{"oldstr": "sample", "types": 3}],
            "typosnum": 1,
            "hastypos": True,
        }
        receipt = _receipt(content)
        session = requests.Session()
        session.get = Mock(return_value=_response(text='{"owner": 123456, "state": 3}'))
        accepted = b"accepted"
        session.post = Mock(return_value=_response(content=accepted))
        client = BodaClient(
            allowed_root="FOLD:new",
            session=session,
        )

        with patch(
            "boda_release._SECURITY_UPDATE_RESPONSE_SHA256",
            hashlib.sha256(accepted).hexdigest(),
        ):
            client.update_security_record(receipt, "documented release")

        data = session.post.call_args.kwargs["data"]
        self.assertEqual(data["owner"], "123456")
        self.assertEqual(data["state"], "3")
        self.assertEqual(data["typosnoteid"], receipt.typosnoteid)
        self.assertEqual(data["filesrc"], receipt.filesrc)
        self.assertEqual(
            data["wbsensitiveresult"],
            _encode_post_param(
                json.dumps(content, ensure_ascii=False, separators=(",", ":"))
            ),
        )
        self.assertEqual(
            data["ignorecontent"],
            _encode_post_param(_build_ignore_content(content)),
        )

    def test_security_reason_empty_is_rejected_before_network(self):
        session = requests.Session()
        session.get = Mock()
        client = BodaClient(
            allowed_root="FOLD:new",
            session=session,
        )

        with self.assertRaises(BodaError):
            client.update_security_record(_receipt(), "  ")
        session.get.assert_not_called()

    def test_security_update_rejects_unknown_success_response(self):
        session = requests.Session()
        session.get = Mock(return_value=_response(text='{"owner": 123456, "state": 3}'))
        session.post = Mock(return_value=_response(content=b"unknown"))
        client = BodaClient(
            allowed_root="FOLD:new",
            session=session,
        )

        with self.assertRaises(BodaError):
            client.update_security_record(_receipt(), "documented release")

    def test_sensitive_values_are_not_in_security_errors(self):
        session = requests.Session()
        session.get = Mock(return_value=_response(text="incomplete"))
        client = BodaClient(
            allowed_root="FOLD:new",
            session=session,
        )

        with self.assertRaises(BodaError) as raised:
            client.update_security_record(_receipt(), "REASON_SECRET")
        message = str(raised.exception)
        self.assertNotIn("REASON_SECRET", message)
        self.assertNotIn("/system/_owners/", message)

    def test_official_post_parameter_encoding(self):
        self.assertEqual(_encode_post_param("abc"), "jWJY")
        self.assertEqual(_encode_post_param("测试"), "VK+L6rW5")
        self.assertEqual(
            _build_ignore_content({"typos": [{"oldstr": "sample", "types": 3}]}),
            '~{"文件内容":{"typeStr":"错别字","old":"“sample”",'
            '"msg":"建议更换为","new":""}}',
        )

    def test_deploy_creates_directories_shallow_first(self):
        class Client:
            def __init__(self):
                self.calls = []

            def list_directory(self):
                self.calls.append(("list", "."))

            def create_directory(self, parent, name, description):
                self.calls.append(("mkdir", str(parent), name))

            def upload_file(self, directory, path, *, overwrite):
                self.calls.append(("upload", str(directory), path.name))
                return _receipt()

            def update_security_record(self, receipt, reason):
                self.calls.append(("security", reason))

            def verify_public(self, entry, public_path):
                self.calls.append(("verify", str(entry.path)))

        release = Release(
            Path("/release"),
            (
                ReleaseFile(PurePosixPath("a/b/file.css"), "0" * 64),
                ReleaseFile(PurePosixPath("index.html"), "1" * 64),
                ReleaseFile(PurePosixPath("index.htm"), "1" * 64),
            ),
        )
        client = Client()

        deploy_release(client, release, "documented release")

        mkdir_calls = [call for call in client.calls if call[0] == "mkdir"]
        self.assertEqual(
            mkdir_calls,
            [("mkdir", ".", "a"), ("mkdir", "a", "b")],
        )
        last_upload = max(
            index for index, call in enumerate(client.calls) if call[0] == "upload"
        )
        first_verify = min(
            index for index, call in enumerate(client.calls) if call[0] == "verify"
        )
        self.assertLess(last_upload, first_verify)

    def test_deploy_verifies_ok_overwrite_without_security_receipt(self):
        class Client:
            def list_directory(self):
                return None

            def upload_file(self, directory, path, *, overwrite):
                return None

            def update_security_record(self, receipt, reason):
                raise AssertionError("security update requires a structured receipt")

            def verify_public(self, entry, public_path=None):
                self.verified = (entry.path, public_path)

        release = Release(
            Path("/release"),
            (ReleaseFile(PurePosixPath("index.html"), "0" * 64),),
        )
        client = Client()

        self.assertEqual(deploy_release(client, release, "documented release"), 1)
        self.assertEqual(client.verified, (PurePosixPath("index.html"), None))

    def test_crud_test_runs_create_upload_verify_delete_order(self):
        client = Mock()
        client.allowed_root = "FOLD:test"
        client.list_directory.side_effect = [
            Namespace(folders=frozenset(), files=frozenset()),
            Namespace(folders=frozenset(), files=frozenset({"B.txt"})),
        ]
        client.create_directory.return_value = True

        self.assertTrue(run_crud_test(client))

        self.assertEqual(
            [entry[0] for entry in client.method_calls],
            [
                "list_directory",
                "create_directory",
                "upload_file",
                "list_directory",
                "delete_file",
                "delete_directory",
            ],
        )
        upload_path = client.upload_file.call_args.args[1]
        self.assertEqual(upload_path.name, "B.txt")

    def test_crud_test_accepts_remote_listing_after_non_json_upload_receipt(self):
        client = Mock()
        client.allowed_root = "FOLD:test"
        client.list_directory.side_effect = [
            Namespace(folders=frozenset(), files=frozenset()),
            Namespace(folders=frozenset(), files=frozenset({"B.txt"})),
        ]
        client.create_directory.return_value = True
        client.upload_file.side_effect = BodaUploadReceiptError("non-JSON receipt")

        self.assertFalse(run_crud_test(client))

        client.delete_file.assert_called_once_with("A", "B.txt")
        client.delete_directory.assert_called_once_with(".", "A")

    def test_crud_test_propagates_other_upload_errors(self):
        client = Mock()
        client.allowed_root = "FOLD:test"
        client.list_directory.return_value = Namespace(
            folders=frozenset(), files=frozenset()
        )
        client.create_directory.return_value = True
        client.upload_file.side_effect = BodaError("upload failed")

        with self.assertRaisesRegex(BodaError, "upload failed"):
            run_crud_test(client)

        client.delete_file.assert_called_once_with("A", "B.txt")
        client.delete_directory.assert_called_once_with(".", "A")

    def test_crud_test_refuses_preexisting_directory_without_writes(self):
        client = Mock()
        client.allowed_root = "FOLD:test"
        client.list_directory.return_value = Namespace(
            folders=frozenset({"A"}), files=frozenset()
        )

        with self.assertRaises(BodaError):
            run_crud_test(client)

        client.create_directory.assert_not_called()
        client.upload_file.assert_not_called()
        client.delete_file.assert_not_called()
        client.delete_directory.assert_not_called()

    def test_crud_test_cleans_up_after_verification_failure(self):
        client = Mock()
        client.allowed_root = "FOLD:test"
        client.list_directory.side_effect = [
            Namespace(folders=frozenset(), files=frozenset()),
            Namespace(folders=frozenset(), files=frozenset()),
        ]
        client.create_directory.return_value = True

        with self.assertRaises(BodaError):
            run_crud_test(client)

        client.delete_file.assert_called_once_with("A", "B.txt")
        client.delete_directory.assert_called_once_with(".", "A")

    def test_crud_test_cleans_up_if_directory_confirmation_fails(self):
        client = Mock()
        client.allowed_root = "FOLD:test"
        client.list_directory.return_value = Namespace(
            folders=frozenset(), files=frozenset()
        )
        client.create_directory.side_effect = BodaError("confirmation failed")

        with self.assertRaises(BodaError):
            run_crud_test(client)

        client.delete_file.assert_called_once_with("A", "B.txt")
        client.delete_directory.assert_called_once_with(".", "A")

    def test_crud_test_cleans_up_before_propagating_keyboard_interrupt(self):
        client = Mock()
        client.allowed_root = "FOLD:test"
        client.list_directory.side_effect = [
            Namespace(folders=frozenset(), files=frozenset()),
            KeyboardInterrupt(),
        ]
        client.create_directory.return_value = True

        with self.assertRaises(KeyboardInterrupt):
            run_crud_test(client)

        client.delete_file.assert_called_once_with("A", "B.txt")
        client.delete_directory.assert_called_once_with(".", "A")

    def test_crud_test_rejects_any_root_other_than_test(self):
        client = Mock()
        client.allowed_root = "FOLD:new"

        with self.assertRaises(BodaError):
            run_crud_test(client)

        client.list_directory.assert_not_called()

    @patch("boda_release.__main__._client")
    def test_crud_cli_requires_confirmation_before_login(self, client):
        with patch("sys.argv", ["boda_release", "crud-test"]):
            self.assertEqual(cli_main(), 1)
        client.assert_not_called()

    @patch("boda_release.__main__.run_crud_test")
    @patch("boda_release.__main__._client")
    def test_crud_cli_calls_helper_after_confirmation(self, client, helper):
        with patch(
            "sys.argv",
            [
                "boda_release",
                "crud-test",
                "--apply",
                "--confirm",
                "BODA_CRUD_TEST",
                "--path-prefix",
                "/test",
            ],
        ):
            self.assertEqual(cli_main(), 0)
        client.assert_called_once()
        self.assertEqual(client.call_args.args[0].path_prefix, "/test")
        helper.assert_called_once_with(client.return_value)


class IncrementalReleaseTest(unittest.TestCase):
    def _release(self, extra=()):
        files = [
            ReleaseFile(PurePosixPath("index.html"), "a" * 64),
            ReleaseFile(PurePosixPath("index.htm"), "a" * 64),
        ]
        files.extend(extra)
        return Release(Path("/tmp/release"), tuple(files))

    def test_state_round_trip_is_canonical(self):
        state = DeploymentState.from_release(
            self._release(), "b" * 40, path_prefix="/site"
        )
        encoded = state.serialize()
        self.assertTrue(encoded.endswith(b"\n"))
        self.assertEqual(DeploymentState.parse(encoded), state)

    def test_state_rejects_duplicate_json_keys(self):
        payload = (
            b'{"schema":1,"schema":1,"commit":"'
            + b"b" * 40
            + b'","dirty":false,"path_prefix":"","files":[]}'
        )
        with self.assertRaises(BodaError):
            DeploymentState.parse(payload)

    def test_state_rejects_oversized_payload(self):
        with self.assertRaises(BodaError):
            DeploymentState.parse(b"x" * (1024 * 1024 + 1))

    def test_state_reader_distinguishes_missing(self):
        client = BodaClient(session=requests.Session())
        with (
            patch("boda_release.requests.get", return_value=_response(status=404)),
            patch("boda_release.time.sleep"),
        ):
            with self.assertRaises(DeploymentStateNotFound):
                client.read_deployment_state()

    def test_state_reader_retries_transient_404(self):
        state = DeploymentState.from_release(self._release(), "b" * 40)
        client = BodaClient(session=requests.Session())
        with (
            patch(
                "boda_release.requests.get",
                side_effect=[
                    _response(status=404),
                    _response(content=state.serialize()),
                ],
            ) as get,
            patch("boda_release.time.sleep") as sleep,
        ):
            self.assertEqual(client.read_deployment_state(), state)
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_state_rejects_reserved_root_tree(self):
        release = self._release(
            (ReleaseFile(PurePosixPath("bodacli-state.txt/child"), "c" * 64),)
        )
        with self.assertRaises(BodaError):
            DeploymentState.from_release(release, "b" * 40)

    def test_state_size_is_checked_during_construction(self):
        extra = tuple(
            ReleaseFile(PurePosixPath(f"file-{index:05d}.txt"), "c" * 64)
            for index in range(12000)
        )
        with self.assertRaises(BodaError):
            DeploymentState.from_release(self._release(extra), "b" * 40)

    def test_incremental_plan_classifies_delta(self):
        old = DeploymentState.from_release(
            self._release((ReleaseFile(PurePosixPath("old.txt"), "c" * 64),)), "b" * 40
        )
        new = self._release((ReleaseFile(PurePosixPath("new.txt"), "d" * 64),))
        plan = compute_incremental_plan(new, old)
        self.assertEqual([e.path.as_posix() for e in plan.uploads], ["new.txt"])
        self.assertEqual([e.path.as_posix() for e in plan.deletes], ["old.txt"])

    def test_incremental_plan_rejects_shape_transition(self):
        old = DeploymentState.from_release(
            self._release((ReleaseFile(PurePosixPath("docs"), "c" * 64),)), "b" * 40
        )
        with self.assertRaises(BodaError):
            compute_incremental_plan(
                self._release(
                    (ReleaseFile(PurePosixPath("docs/page.html"), "d" * 64),)
                ),
                old,
            )

    def test_publish_state_verifies_receipt_public_path(self):
        client = Mock()
        client.upload_file.return_value = _receipt()
        client.list_directory.return_value = DirectoryListing(
            "FOLD:", frozenset(), frozenset({"bodacli-state.txt"})
        )
        state = DeploymentState.from_release(self._release(), "b" * 40)
        publish_deployment_state(client, state, "reason")
        self.assertEqual(
            client.verify_public.call_args.args[1], PurePosixPath("new/index.html")
        )

    def test_incremental_deploy_writes_state_last(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_bytes(b"a")
            (root / "index.htm").write_bytes(b"a")
            (root / "new.txt").write_bytes(b"new")
            new = Release(
                root,
                (
                    ReleaseFile(PurePosixPath("index.html"), "a" * 64),
                    ReleaseFile(PurePosixPath("index.htm"), "a" * 64),
                    ReleaseFile(PurePosixPath("new.txt"), "d" * 64),
                ),
            )
            previous = DeploymentState.from_release(
                self._release((ReleaseFile(PurePosixPath("old.txt"), "c" * 64),)),
                "b" * 40,
            )
            events = []
            client = Mock(path_prefix="")

            def listing(_directory="."):
                files = (
                    frozenset({"bodacli-state.txt"})
                    if "upload:bodacli-state.txt" in events
                    else frozenset()
                )
                return DirectoryListing("FOLD:", frozenset(), files)

            client.list_directory.side_effect = listing

            def upload(_directory, path, *, overwrite):
                events.append(f"upload:{path.name}")
                return None

            def verify(entry, public_path=None):
                events.append(f"verify:{entry.path.as_posix()}")

            def delete(directory, name):
                events.append(f"delete:{PurePosixPath(directory) / name}")
                return True

            def verify_absent(entry):
                events.append(f"absent:{entry.path.as_posix()}")

            client.upload_file.side_effect = upload
            client.verify_public.side_effect = verify
            client.verify_public_absent.side_effect = verify_absent
            client.read_deployment_state.return_value = previous
            client.delete_file.side_effect = delete
            deploy_incremental(client, new, previous, "c" * 40, "reason")

            self.assertEqual(
                events,
                [
                    "verify:old.txt",
                    "verify:index.html",
                    "verify:index.htm",
                    "upload:new.txt",
                    "verify:new.txt",
                    "delete:old.txt",
                    "absent:old.txt",
                    "upload:bodacli-state.txt",
                    "verify:bodacli-state.txt",
                ],
            )

    def test_incremental_deploy_rejects_unmanaged_collision(self):
        release = self._release((ReleaseFile(PurePosixPath("new.txt"), "d" * 64),))
        previous = DeploymentState.from_release(self._release(), "b" * 40)
        client = Mock(path_prefix="")
        client.list_directory.return_value = DirectoryListing(
            "FOLD:", frozenset(), frozenset({"new.txt"})
        )
        with self.assertRaises(BodaError):
            deploy_incremental(client, release, previous, "c" * 40, "reason")
        client.upload_file.assert_not_called()

    def test_incremental_deploy_treats_delete_false_as_drift(self):
        release = self._release()
        previous = DeploymentState.from_release(
            self._release((ReleaseFile(PurePosixPath("old.txt"), "c" * 64),)), "b" * 40
        )
        client = Mock(path_prefix="")
        client.list_directory.return_value = DirectoryListing(
            "FOLD:", frozenset(), frozenset({"old.txt"})
        )
        client.verify_public.return_value = None
        client.delete_file.return_value = False
        client.read_deployment_state.return_value = previous
        with self.assertRaises(BodaError):
            deploy_incremental(client, release, previous, "c" * 40, "reason")
        client.upload_file.assert_not_called()

    def test_incremental_deploy_rejects_unchanged_remote_drift(self):
        release = self._release()
        previous = DeploymentState.from_release(self._release(), "b" * 40)
        client = Mock(path_prefix="")
        client.list_directory.return_value = DirectoryListing(
            "FOLD:", frozenset(), frozenset()
        )
        client.verify_public.side_effect = BodaError("drift")

        with self.assertRaises(BodaError):
            deploy_incremental(client, release, previous, "c" * 40, "reason")

        client.upload_file.assert_not_called()
        client.delete_file.assert_not_called()

    def test_incremental_deploy_rejects_changed_state_before_writes(self):
        release = self._release()
        previous = DeploymentState.from_release(self._release(), "b" * 40)
        changed = DeploymentState.from_release(self._release(), "c" * 40)
        client = Mock(path_prefix="")
        client.list_directory.return_value = DirectoryListing(
            "FOLD:", frozenset(), frozenset()
        )
        client.verify_public.return_value = None
        client.read_deployment_state.return_value = changed

        with self.assertRaises(BodaError):
            deploy_incremental(client, release, previous, "d" * 40, "reason")

        client.upload_file.assert_not_called()
        client.delete_file.assert_not_called()

    @patch("boda_release.time.sleep")
    @patch("boda_release.requests.get")
    def test_public_deletion_retries_cached_content(self, get, sleep):
        get.side_effect = [
            _response(content=b"old"),
            _response(status=404),
            _response(status=404),
        ]
        client = BodaClient(session=requests.Session())

        client.verify_public_absent(
            ReleaseFile(PurePosixPath("old.txt"), hashlib.sha256(b"old").hexdigest())
        )

        self.assertEqual(get.call_count, 3)
        self.assertEqual(sleep.call_count, 2)
        sleep.assert_called_with(1)

    def test_incremental_deploy_validates_before_network(self):
        previous = DeploymentState.from_release(self._release(), "b" * 40)
        client = Mock(path_prefix="")

        with self.assertRaises(BodaError):
            deploy_incremental(client, self._release(), previous, "bad", "reason")
        with self.assertRaises(BodaError):
            deploy_incremental(client, self._release(), previous, "c" * 40, " ")

        client.list_directory.assert_not_called()
        client.upload_file.assert_not_called()

    def test_dirty_state_cannot_be_incremental_baseline(self):
        previous = DeploymentState.from_release(self._release(), "b" * 40, dirty=True)
        client = Mock(path_prefix="")

        with self.assertRaises(BodaError):
            deploy_incremental(client, self._release(), previous, "c" * 40, "reason")

        client.list_directory.assert_not_called()

    def test_state_reader_rejects_prefix_mismatch(self):
        state = DeploymentState.from_release(
            self._release(), "b" * 40, path_prefix="/other"
        )
        client = BodaClient(path_prefix="/new", session=requests.Session())
        with patch(
            "boda_release.requests.get",
            return_value=_response(content=state.serialize()),
        ):
            with self.assertRaises(BodaError):
                client.read_deployment_state()

    @patch("boda_release.__main__._git_succeeds", side_effect=[True, True])
    @patch(
        "boda_release.__main__._git_output",
        side_effect=["b" * 40, "", "M\tsite/layouts/_default/baseof.html"],
    )
    def test_git_snapshot_reports_source_diff(self, git_output, git_succeeds):
        snapshot = _git_snapshot("a" * 40)

        self.assertEqual(snapshot.commit, "b" * 40)
        self.assertFalse(snapshot.dirty)
        self.assertEqual(snapshot.changes, ("M\tsite/layouts/_default/baseof.html",))

    @patch("boda_release.__main__._git_succeeds", side_effect=[True, False])
    @patch("boda_release.__main__._git_output", side_effect=["b" * 40, ""])
    def test_git_snapshot_rejects_nonancestor(self, git_output, git_succeeds):
        with self.assertRaises(BodaError):
            _git_snapshot("a" * 40)

    @patch(
        "boda_release.__main__._git_snapshot",
        return_value=GitSnapshot("c" * 40, False),
    )
    def test_release_snapshot_rejects_stale_artifact(self, git_snapshot):
        with self.assertRaises(BodaError):
            _release_snapshot(_release_fixture())

    @patch(
        "boda_release.__main__._git_snapshot",
        return_value=GitSnapshot("b" * 40, False),
    )
    def test_release_snapshot_requires_build_metadata(self, git_snapshot):
        with self.assertRaises(BodaError):
            _release_snapshot(self._release())


if __name__ == "__main__":
    unittest.main()
