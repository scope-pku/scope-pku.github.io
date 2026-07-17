import hashlib
import json
import os
import sys
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "deploy_github_release.sh"
SHA = "a" * 40


class DeployGithubReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.log"
        self.zip = self.root / "release.zip"
        with zipfile.ZipFile(self.zip, "w") as archive:
            build = json.dumps({"schema": 1, "commit": SHA}).encode()
            archive.writestr("BODACLI_BUILD.json", build)
            archive.writestr(
                "SHA256SUMS", hashlib.sha256(b"site").hexdigest() + "  ./index.html\n"
            )
            archive.writestr("index.html", "site")
        self._commands()

    def tearDown(self):
        self.tmp.cleanup()

    def command(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\nset -eu\n" + body)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def _commands(self):
        self.command(
            "curl",
            r"""
url=""
out=""
method=GET
prev=
max_time=
for arg in "$@"; do
  case "$arg" in
    --request) prev=request;;
    POST) method=POST;;
    --output) prev=output;;
    --max-time) prev=max_time;;
    http*) url=$arg;;
    *)
      if [ "$prev" = output ]; then out=$arg; prev=
      elif [ "$prev" = max_time ]; then max_time=$arg; prev=
      fi;;
  esac
done
printf 'curl:%s:%s:max=%s\n' "$method" "$url" "$max_time" >> "$CALL_LOG"
case "$url" in
  */dispatches) printf '{"workflow_run_id":42,"html_url":"https://github.com/scope-pku/scope-pku.github.io/actions/runs/42"}' ;;
  */actions/runs/42/artifacts*) printf '{"artifacts":[{"name":"boda-site-%s","expired":false,"archive_download_url":"https://api.github.com/archive/42"}]}' "$HEAD_SHA" ;;
  */actions/runs/42) printf '{"path":".github/workflows/boda-release.yml","event":"workflow_dispatch","head_branch":"main","head_sha":"%s","html_url":"https://github.com/scope-pku/scope-pku.github.io/actions/runs/42","status":"%s","conclusion":"%s"}' "$HEAD_SHA" "${RUN_STATUS:-completed}" "${RUN_CONCLUSION:-success}" ;;
  */archive/42) cp "$RELEASE_ZIP" "$out" ;;
  *) echo "unexpected curl URL" >&2; exit 1 ;;
esac
""",
        )
        self.command(
            "git",
            r"""
printf 'git:%s github=%s boda=%s\n' "$*" "${GITHUB_TOKEN:+set}" "${BODA_IAAA_PASSWORD:+set}" >> "$CALL_LOG"
while [ "$1" = -c ]; do shift 2; done
if [ "$1" = -C ]; then shift 2; fi
case "$1" in
  rev-parse) printf '%s\n' "$FAKE_REPO" ;;
  remote) printf '%s\n' "${FAKE_ORIGIN:-https://github.com/scope-pku/scope-pku.github.io.git}" ;;
  fetch) : ;;
  worktree) mkdir -p "$4" ;;
  clone) mkdir -p "$5" ;;
  checkout) : ;;
esac
""",
        )
        self.command(
            "python3",
            r"""
if [ "$1" = -m ] && [ "$2" = venv ]; then
  mkdir -p "$3/bin"
  cat > "$3/bin/python" <<'PY'
#!/bin/sh
printf 'python:%s cwd=%s github=%s boda=%s\n' "$*" "$PWD" "${GITHUB_TOKEN:+set}" "${BODA_IAAA_PASSWORD:+set}" >> "$CALL_LOG"
exit 0
PY
  chmod +x "$3/bin/python"
elif [ "$1" = -m ]; then
  printf 'python:%s cwd=%s github=%s boda=%s\n' "$*" "$PWD" "${GITHUB_TOKEN:+set}" "${BODA_IAAA_PASSWORD:+set}" >> "$CALL_LOG"
  exit 0
else
  exec "$REAL_PYTHON" "$@"
fi
""",
        )

    def execute(self, *args, **extra):
        env = os.environ.copy()
        env.update(
            {
                "PATH": str(self.bin) + os.pathsep + env["PATH"],
                "CALL_LOG": str(self.log),
                "FAKE_REPO": str(self.root / "repo"),
                "HEAD_SHA": SHA,
                "RELEASE_ZIP": str(self.zip),
                "GITHUB_TOKEN": "secret-token",
                "REAL_PYTHON": sys.executable,
                "BODA_RELEASE_POLL_SECONDS": "0",
            }
        )
        env.update(extra)
        return subprocess.run(
            [str(SCRIPT), *args], cwd=self.root, env=env, text=True, capture_output=True
        )

    def test_shell_syntax_and_missing_token(self):
        syntax = subprocess.run(
            ["sh", "-n", str(SCRIPT)], text=True, capture_output=True
        )
        self.assertEqual(syntax.returncode, 0, syntax.stderr)
        result = self.execute(GITHUB_TOKEN="", GH_TOKEN="")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GITHUB_TOKEN or GH_TOKEN is required", result.stderr)

    def test_dispatch_poll_and_artifact_download(self):
        result = self.execute("--plan-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text()
        self.assertIn("dispatches", calls)
        self.assertIn("/actions/runs/42", calls)
        self.assertIn("archive/42", calls)
        self.assertNotIn("secret-token", calls + result.stdout + result.stderr)

    def test_run_id_skips_dispatch(self):
        result = self.execute("--run-id", "42", "--plan-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("dispatches", self.log.read_text())

    def test_metadata_and_artifact_errors_fail_closed(self):
        self.command(
            "curl",
            r"""
url=""; out=""; prev=
for arg in "$@"; do case "$arg" in --output) prev=output;; http*) url=$arg;; *) [ "$prev" = output ] && out=$arg && prev=;; esac; done
case "$url" in */actions/runs/42) printf '{"path":".github/workflows/wrong.yml","event":"workflow_dispatch","head_branch":"main","head_sha":"%s","html_url":"u","status":"completed","conclusion":"success"}' "$HEAD_SHA";; *) cp "$RELEASE_ZIP" "$out";; esac
""",
        )
        result = self.execute("--run-id", "42")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unexpected workflow", result.stderr)

    def test_ssh_origin_uses_token_backed_https_fetch(self):
        result = self.execute(
            "--run-id",
            "42",
            "--plan-only",
            FAKE_ORIGIN="git@github.com:scope-pku/scope-pku.github.io.git",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "fetch --no-tags https://github.com/scope-pku/scope-pku.github.io.git",
            self.log.read_text(),
        )

    def test_checkout_commands_disable_hooks(self):
        result = self.execute("--run-id", "42", "--plan-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        worktree = next(
            line
            for line in self.log.read_text().splitlines()
            if " worktree add " in line
        )
        self.assertIn("-c core.hooksPath=/dev/null", worktree)
        self.assertNotIn("github=set", worktree)
        self.assertNotIn("boda=set", worktree)

        self.log.write_text("")
        result = self.execute(
            "--run-id", "42", "--plan-only", FAKE_ORIGIN="https://example.invalid/repo"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        checkout = next(
            line
            for line in self.log.read_text().splitlines()
            if " checkout --detach " in line
        )
        self.assertIn("-c core.hooksPath=/dev/null", checkout)
        self.assertNotIn("github=set", checkout)
        self.assertNotIn("boda=set", checkout)

    def test_git_auth_and_pip_hide_boda_credentials(self):
        result = self.execute(
            "--run-id", "42", "--plan-only", BODA_IAAA_PASSWORD="boda-secret"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = self.log.read_text().splitlines()
        fetch = next(line for line in lines if " fetch --no-tags " in line)
        self.assertIn("github=set", fetch)
        self.assertNotIn("boda=set", fetch)
        self.assertIn("-c credential.helper=", fetch)
        materialize = next(line for line in lines if " worktree add " in line)
        self.assertNotIn("github=set", materialize)
        self.assertNotIn("boda=set", materialize)
        pip = next(line for line in lines if "-m pip install" in line)
        self.assertNotIn("github=set", pip)
        self.assertNotIn("boda=set", pip)
        plan = next(line for line in lines if "-m boda_release plan" in line)
        self.assertNotIn("github=set", plan)
        self.assertIn("boda=set", plan)

    def test_poll_request_uses_lower_timeout(self):
        result = self.execute(
            "--run-id",
            "42",
            "--plan-only",
            BODA_RELEASE_TIMEOUT_SECONDS="10",
            BODA_RELEASE_REQUEST_TIMEOUT_SECONDS="3",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        run_request = next(
            line
            for line in self.log.read_text().splitlines()
            if "/actions/runs/42:max=" in line
        )
        self.assertTrue(run_request.endswith("max=3"), run_request)

    def test_workflow_poll_respects_deadline(self):
        result = self.execute(
            "--run-id",
            "42",
            "--plan-only",
            RUN_STATUS="queued",
            RUN_CONCLUSION="",
            BODA_RELEASE_TIMEOUT_SECONDS="1",
            BODA_RELEASE_POLL_SECONDS="2",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("timed out waiting for workflow run", result.stderr)

    def test_confirmation_happens_before_deploy(self):
        result = self.execute("--run-id", "42", "--confirm", "WRONG")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid deployment confirmation", result.stderr)
        calls = self.log.read_text()
        self.assertNotIn(" boda_release deploy", calls)

    def test_plan_probe_deploy_order(self):
        result = self.execute("--run-id", "42", "--confirm", "DEPLOY_NONATOMIC")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [
            line
            for line in self.log.read_text().splitlines()
            if line.startswith("python:") and "-m pip" not in line
        ]
        self.assertIn("plan", calls[0])
        self.assertIn("probe", calls[1])
        self.assertIn("deploy", calls[2])
        self.assertIn("path=/new", result.stdout)

    def test_probe_only_has_no_deploy(self):
        result = self.execute("--run-id", "42", "--probe-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = [
            line
            for line in self.log.read_text().splitlines()
            if line.startswith("python:") and "-m pip" not in line
        ]
        self.assertEqual(len(calls), 2)
        self.assertNotIn("deploy", "\n".join(calls))


if __name__ == "__main__":
    unittest.main()
