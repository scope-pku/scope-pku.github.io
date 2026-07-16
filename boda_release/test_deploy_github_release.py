import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "deploy_github_release.sh"


class DeployGithubReleaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        self.log = Path(self.tmp.name) / "calls.log"

    def tearDown(self):
        self.tmp.cleanup()

    def command(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\nset -eu\n" + body)
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def base_commands(self, metadata=None):
        metadata = metadata or {
            "workflowName": "Boda release package",
            "event": "workflow_dispatch",
            "headBranch": "main",
            "headSha": "a" * 40,
            "url": "https://github.com/example/repo/actions/runs/42",
            "status": "completed",
            "conclusion": "success",
        }
        self.metadata = metadata
        self.command(
            "gh",
            f"""\ncase "$1" in
  --version) printf 'gh version %s (test)\n' "${{GH_VERSION:-2.96.0}}" ;;
  workflow)
    [ "$2" = run ]
    printf 'https://github.com/example/repo/actions/runs/42\n'
    ;;
  run)
    case "$2" in
      watch) printf 'watch:%s\n' "$3" >> "$CALL_LOG" ;;
      view) cat <<'JSON'
{json.dumps(metadata)}
JSON
        ;;
      download) mkdir -p "$7"; printf '{{"commit":"%s"}}\n' "${{HEAD_SHA}}" > "$7/BODACLI_BUILD.json"; : > "$7/SHA256SUMS" ;;
    esac
    ;;
esac
""",
        )
        self.command(
            "git",
            """printf 'git:%s\\n' "$*" >> "$CALL_LOG"
case "$1" in
  worktree) [ "$2" = add ] && mkdir -p "$4" ;;
esac
""",
        )
        self.command(
            "python3",
            """if [ "$1" = -c ]; then
  input=$(cat)
  if [ -n "$input" ]; then
    printf '%s\\t' "$WORKFLOW_NAME"; printf '%s\\t' "$WORKFLOW_EVENT"; printf '%s\\t' "$HEAD_BRANCH"; printf '%s\\t' "$HEAD_SHA"; printf '%s\\t' "$RUN_URL"; printf '%s\\t' "$RUN_STATUS"; printf '%s\\n' "$RUN_CONCLUSION"
  else
    printf '%s\\n' "$HEAD_SHA"
  fi
elif [ "$1" = -m ] && [ "$2" = venv ]; then
  mkdir -p "$3/bin"
  cat > "$3/bin/python" <<'PY'
#!/bin/sh
printf 'python:%s cwd=%s\\n' "$*" "$PWD" >> "$CALL_LOG"
exit 0
PY
  chmod +x "$3/bin/python"
fi
""",
        )

    def execute(self, *args, **env):
        full_env = os.environ.copy()
        full_env.update(
            {
                "PATH": str(self.bin) + os.pathsep + full_env["PATH"],
                "CALL_LOG": str(self.log),
                "HEAD_SHA": self.metadata["headSha"],
                "WORKFLOW_NAME": self.metadata["workflowName"],
                "WORKFLOW_EVENT": self.metadata["event"],
                "HEAD_BRANCH": self.metadata["headBranch"],
                "RUN_STATUS": self.metadata["status"],
                "RUN_CONCLUSION": self.metadata["conclusion"],
                "RUN_URL": self.metadata["url"],
            }
        )
        full_env.update(env)
        return subprocess.run(
            [str(SCRIPT), *args], cwd=ROOT, env=full_env, text=True, capture_output=True
        )

    def test_unknown_and_mutually_exclusive_options(self):
        self.base_commands()
        unknown = self.execute("--no-such-option")
        self.assertNotEqual(unknown.returncode, 0)
        self.assertIn("unknown argument", unknown.stderr)
        both = self.execute("--plan-only", "--probe-only")
        self.assertNotEqual(both.returncode, 0)
        self.assertIn("mutually exclusive", both.stderr)
        incremental_read_only = self.execute("--incremental", "--plan-only")
        self.assertNotEqual(incremental_read_only.returncode, 0)
        self.assertIn("cannot be combined", incremental_read_only.stderr)
        confirmed_read_only = self.execute(
            "--probe-only", "--confirm", "DEPLOY_NONATOMIC"
        )
        self.assertNotEqual(confirmed_read_only.returncode, 0)
        self.assertIn("cannot be combined", confirmed_read_only.stderr)
        invalid_run = self.execute("--run-id", "not-a-number", "--plan-only")
        self.assertNotEqual(invalid_run.returncode, 0)
        self.assertIn("digits only", invalid_run.stderr)

    def test_default_dispatch_requires_modern_gh_and_uses_returned_run_id(self):
        self.base_commands()
        old = self.execute("--plan-only", GH_VERSION="2.86.0")
        self.assertNotEqual(old.returncode, 0)
        self.assertIn("gh 2.87 or newer", old.stderr)

        current = self.execute("--plan-only")
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertIn("watch:42", self.log.read_text())

    def test_wrong_confirmation_fails_before_deploy(self):
        self.base_commands()
        result = self.execute("--run-id", "42", "--confirm", "WRONG")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid deployment confirmation", result.stderr)
        log = self.log.read_text() if self.log.exists() else ""
        self.assertFalse(
            any("-m boda_release deploy" in line for line in log.splitlines())
        )

    def test_run_metadata_rejects_wrong_workflow_branch_event_and_success(self):
        cases = [
            (
                {
                    "workflowName": "Other",
                    "event": "workflow_dispatch",
                    "headBranch": "main",
                    "headSha": "a" * 40,
                    "url": "u",
                    "status": "completed",
                    "conclusion": "success",
                },
                "unexpected workflow",
            ),
            (
                {
                    "workflowName": "Boda release package",
                    "event": "push",
                    "headBranch": "main",
                    "headSha": "a" * 40,
                    "url": "u",
                    "status": "completed",
                    "conclusion": "success",
                },
                "non-manual",
            ),
            (
                {
                    "workflowName": "Boda release package",
                    "event": "workflow_dispatch",
                    "headBranch": "dev",
                    "headSha": "a" * 40,
                    "url": "u",
                    "status": "completed",
                    "conclusion": "success",
                },
                "not on main",
            ),
            (
                {
                    "workflowName": "Boda release package",
                    "event": "workflow_dispatch",
                    "headBranch": "main",
                    "headSha": "a" * 40,
                    "url": "u",
                    "status": "completed",
                    "conclusion": "failure",
                },
                "unsuccessful",
            ),
        ]
        for metadata, message in cases:
            with self.subTest(message=message):
                self.base_commands(metadata)
                result = self.execute("--run-id", "42")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(message, result.stderr)

    def test_plan_probe_deploy_order_and_summary(self):
        self.base_commands()
        result = self.execute("--run-id", "42", "--confirm", "DEPLOY_NONATOMIC")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text().splitlines()
        python_calls = [
            line
            for line in calls
            if line.startswith("python:") and "-m pip" not in line
        ]
        self.assertIn("-m boda_release plan", python_calls[0])
        self.assertIn("-m boda_release probe", python_calls[1])
        self.assertIn("-m boda_release deploy", python_calls[2])
        self.assertIn("DEPLOY_NONATOMIC", python_calls[2])
        self.assertIn("path=/new", result.stdout)
        self.assertIn("sha=" + "a" * 40, result.stdout)

    def test_probe_only_runs_plan_then_probe_without_deploy(self):
        self.base_commands()
        result = self.execute("--run-id", "42", "--probe-only")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text().splitlines()
        python_calls = [
            line
            for line in calls
            if line.startswith("python:") and "-m pip" not in line
        ]
        self.assertEqual(len(python_calls), 2)
        self.assertIn("-m boda_release plan", python_calls[0])
        self.assertIn("-m boda_release probe", python_calls[1])


if __name__ == "__main__":
    unittest.main()
