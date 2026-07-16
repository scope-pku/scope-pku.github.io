#!/bin/sh
set -eu
umask 077

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

for command in gh git python3; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "required command not found: $command" >&2
    exit 1
  fi
done

run_id=
mode=full
plan_only=false
probe_only=false
confirm=

while [ "$#" -gt 0 ]; do
  case "$1" in
    --run-id)
      [ "$#" -ge 2 ] || { echo "--run-id requires an ID" >&2; exit 2; }
      [ -n "$2" ] || { echo "--run-id requires an ID" >&2; exit 2; }
      [ -z "$run_id" ] || { echo "--run-id specified more than once" >&2; exit 2; }
      run_id=$2
      shift 2
      ;;
    --incremental)
      [ "$mode" = full ] || { echo "deployment mode options are mutually exclusive" >&2; exit 2; }
      mode=incremental
      shift
      ;;
    --plan-only)
      [ "$probe_only" = false ] || { echo "--plan-only and --probe-only are mutually exclusive" >&2; exit 2; }
      plan_only=true
      shift
      ;;
    --probe-only)
      [ "$plan_only" = false ] || { echo "--plan-only and --probe-only are mutually exclusive" >&2; exit 2; }
      probe_only=true
      shift
      ;;
    --confirm)
      [ "$#" -ge 2 ] || { echo "--confirm requires a token" >&2; exit 2; }
      [ -z "$confirm" ] || { echo "--confirm specified more than once" >&2; exit 2; }
      confirm=$2
      shift 2
      ;;
    --)
      shift
      [ "$#" -eq 0 ] || { echo "unexpected argument: $1" >&2; exit 2; }
      ;;
    -*|*)
      echo "unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ -n "$run_id" ]; then
  case "$run_id" in
    *[!0-9]*) echo "--run-id must contain digits only" >&2; exit 2 ;;
  esac
fi
if [ "$mode" = incremental ] && { [ "$plan_only" = true ] || [ "$probe_only" = true ]; }; then
  echo "--incremental cannot be combined with read-only modes" >&2
  exit 2
fi
if [ -n "$confirm" ] && { [ "$plan_only" = true ] || [ "$probe_only" = true ]; }; then
  echo "--confirm cannot be combined with read-only modes" >&2
  exit 2
fi

if [ -z "$run_id" ]; then
  gh_version=$(gh --version | sed -n '1s/^gh version \([0-9][0-9]*\)\.\([0-9][0-9]*\).*/\1 \2/p')
  [ -n "$gh_version" ] || { echo "could not determine gh version" >&2; exit 1; }
  set -- $gh_version
  if [ "$1" -lt 2 ] || { [ "$1" -eq 2 ] && [ "$2" -lt 87 ]; }; then
    echo "gh 2.87 or newer is required to trigger a workflow; upgrade gh or use --run-id" >&2
    exit 1
  fi
  dispatch=$(gh workflow run boda-release.yml --ref main)
  run_id=$(printf '%s\n' "$dispatch" | sed -n 's#.*runs/\([0-9][0-9]*\).*#\1#p' | tail -n 1)
  if [ -z "$run_id" ]; then
    echo "gh workflow run did not return a run URL" >&2
    exit 1
  fi
fi

gh run watch "$run_id" --exit-status
metadata=$(gh run view "$run_id" --json workflowName,event,headBranch,headSha,url,status,conclusion)
meta_fields=$(printf '%s' "$metadata" | python3 -c '
import json, sys
m = json.load(sys.stdin)
values = []
for key in ("workflowName", "event", "headBranch", "headSha", "url", "status", "conclusion"):
    value = m.get(key, "")
    if not isinstance(value, str):
        value = str(value)
    values.append(value.replace("\\", "\\\\").replace("\t", " ").replace("\n", " "))
print("\t".join(values))
')
OLDIFS=$IFS
IFS=$(printf '\t')
set -- $meta_fields
IFS=$OLDIFS
workflow_name=$1
workflow_event=$2
head_branch=$3
head_sha=$4
run_url=$5
run_status=$6
run_conclusion=$7

[ "$workflow_name" = "Boda release package" ] || { echo "refusing unexpected workflow: $workflow_name" >&2; exit 1; }
[ "$workflow_event" = "workflow_dispatch" ] || { echo "refusing non-manual workflow event: $workflow_event" >&2; exit 1; }
[ "$head_branch" = "main" ] || { echo "refusing workflow run not on main: $head_branch" >&2; exit 1; }
[ "$run_status" = "completed" ] || { echo "refusing incomplete workflow run: $run_status" >&2; exit 1; }
[ "$run_conclusion" = "success" ] || { echo "refusing unsuccessful workflow run: $run_conclusion" >&2; exit 1; }
[ "${#head_sha}" -eq 40 ] || { echo "refusing invalid workflow head SHA" >&2; exit 1; }
case "$head_sha" in
  *[!0-9a-fA-F]*) echo "refusing invalid workflow head SHA" >&2; exit 1 ;;
esac
[ -n "$run_url" ] || { echo "workflow run has no URL" >&2; exit 1; }

work_tmp=$(mktemp -d "${TMPDIR:-/tmp}/boda-release.XXXXXX")
worktree=$work_tmp/worktree
venv=$work_tmp/venv
artifact=$work_tmp/artifact
cleanup() {
  if [ -n "${worktree:-}" ] && [ -d "$worktree" ]; then
    git worktree remove --force "$worktree" >/dev/null 2>&1 || true
  fi
  if [ -n "${work_tmp:-}" ] && [ -d "$work_tmp" ]; then
    rm -rf "$work_tmp"
  fi
}
trap cleanup EXIT HUP INT TERM
mkdir -p "$artifact"
gh run download "$run_id" --name "boda-site-$head_sha" --dir "$artifact"
[ -f "$artifact/BODACLI_BUILD.json" ] || { echo "artifact missing BODACLI_BUILD.json" >&2; exit 1; }
[ -f "$artifact/SHA256SUMS" ] || { echo "artifact missing SHA256SUMS" >&2; exit 1; }
artifact_sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("commit", ""))' "$artifact/BODACLI_BUILD.json")
[ "$artifact_sha" = "$head_sha" ] || { echo "artifact commit does not match workflow head SHA" >&2; exit 1; }

git fetch --no-tags origin "$head_sha"
git worktree add --detach "$worktree" "$head_sha"
if [ -f "$root/.env" ]; then
  cp "$root/.env" "$worktree/.env"
  chmod 600 "$worktree/.env"
fi
python3 -m venv "$venv"
"$venv/bin/python" -m pip install --disable-pip-version-check -r "$worktree/boda_release/requirements.txt"

printf 'run=%s\nsha=%s\nmode=%s\npath=/new\n' "$run_url" "$head_sha" "$mode"

export BODA_PATH_PREFIX=/new
(cd "$worktree" && "$venv/bin/python" -m boda_release plan "$artifact")
if [ "$plan_only" = false ]; then
  (cd "$worktree" && "$venv/bin/python" -m boda_release probe --path-prefix /new)
  if [ "$probe_only" = false ]; then
    expected=DEPLOY_NONATOMIC
    if [ "$mode" = incremental ]; then expected=DEPLOY_INCREMENTAL; fi
    if [ -z "$confirm" ]; then
      if [ ! -t 0 ]; then
        echo "deployment confirmation requires a TTY or --confirm" >&2
        exit 2
      fi
      printf 'Type %s to deploy to /new: ' "$expected" >&2
      IFS= read -r confirm
    fi
    [ "$confirm" = "$expected" ] || { echo "invalid deployment confirmation" >&2; exit 2; }
    if [ "$mode" = incremental ]; then
      (cd "$worktree" && "$venv/bin/python" -m boda_release deploy "$artifact" --incremental --path-prefix /new --apply --confirm "$confirm")
    else
      (cd "$worktree" && "$venv/bin/python" -m boda_release deploy "$artifact" --path-prefix /new --apply --confirm "$confirm")
    fi
  fi
fi

