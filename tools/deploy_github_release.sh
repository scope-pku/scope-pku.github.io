#!/bin/sh
set -eu
umask 077

for command in curl git python3; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "required command not found: $command" >&2
    exit 1
  fi
done

token=${GITHUB_TOKEN:-${GH_TOKEN:-}}
[ -n "$token" ] || { echo "GITHUB_TOKEN or GH_TOKEN is required" >&2; exit 1; }
api=https://api.github.com/repos/scope-pku/scope-pku.github.io
run_id=
mode=full
plan_only=false
probe_only=false
confirm=
timeout_seconds=${BODA_RELEASE_TIMEOUT_SECONDS:-1800}
poll_seconds=${BODA_RELEASE_POLL_SECONDS:-5}
request_timeout_seconds=${BODA_RELEASE_REQUEST_TIMEOUT_SECONDS:-300}

case "$timeout_seconds" in *[!0-9]*|'') echo "BODA_RELEASE_TIMEOUT_SECONDS must be a positive integer" >&2; exit 2;; esac
[ "$timeout_seconds" -gt 0 ] || { echo "BODA_RELEASE_TIMEOUT_SECONDS must be a positive integer" >&2; exit 2; }
case "$poll_seconds" in *[!0-9]*|'') echo "BODA_RELEASE_POLL_SECONDS must be a non-negative integer" >&2; exit 2;; esac
case "$request_timeout_seconds" in *[!0-9]*|'') echo "BODA_RELEASE_REQUEST_TIMEOUT_SECONDS must be a positive integer" >&2; exit 2;; esac
[ "$request_timeout_seconds" -gt 0 ] || { echo "BODA_RELEASE_REQUEST_TIMEOUT_SECONDS must be a positive integer" >&2; exit 2; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --run-id)
      [ "$#" -ge 2 ] || { echo "--run-id requires an ID" >&2; exit 2; }
      [ -n "$2" ] || { echo "--run-id requires an ID" >&2; exit 2; }
      [ -z "$run_id" ] || { echo "--run-id specified more than once" >&2; exit 2; }
      run_id=$2; shift 2;;
    --incremental)
      [ "$mode" = full ] || { echo "deployment mode options are mutually exclusive" >&2; exit 2; }
      mode=incremental; shift;;
    --plan-only)
      [ "$probe_only" = false ] || { echo "--plan-only and --probe-only are mutually exclusive" >&2; exit 2; }
      plan_only=true; shift;;
    --probe-only)
      [ "$plan_only" = false ] || { echo "--plan-only and --probe-only are mutually exclusive" >&2; exit 2; }
      probe_only=true; shift;;
    --confirm)
      [ "$#" -ge 2 ] || { echo "--confirm requires a token" >&2; exit 2; }
      [ -z "$confirm" ] || { echo "--confirm specified more than once" >&2; exit 2; }
      confirm=$2; shift 2;;
    --)
      shift; [ "$#" -eq 0 ] || { echo "unexpected argument: $1" >&2; exit 2; };;
    *) echo "unknown argument: $1" >&2; exit 2;;
  esac
done

if [ -n "$run_id" ]; then
  case "$run_id" in *[!0-9]*) echo "--run-id must contain digits only" >&2; exit 2;; esac
fi
if [ "$mode" = incremental ] && { [ "$plan_only" = true ] || [ "$probe_only" = true ]; }; then
  echo "--incremental cannot be combined with read-only modes" >&2; exit 2
fi
if [ -n "$confirm" ] && { [ "$plan_only" = true ] || [ "$probe_only" = true ]; }; then
  echo "--confirm cannot be combined with read-only modes" >&2; exit 2
fi

curl_api() {
  method=$1; url=$2; body=${3:-}; max_time=${4:-$request_timeout_seconds}
  if [ "$method" = POST ]; then
    printf 'Authorization: Bearer %s\n' "$token" | curl --fail --silent --show-error --location \
      --connect-timeout 15 --max-time "$max_time" --request POST \
      --header @- --header 'Accept: application/vnd.github+json' \
      --header 'Content-Type: application/json' --data "$body" "$url"
  else
    printf 'Authorization: Bearer %s\n' "$token" | curl --fail --silent --show-error --location \
      --connect-timeout 15 --max-time "$max_time" \
      --header @- --header 'Accept: application/vnd.github+json' "$url"
  fi
}

if [ -z "$run_id" ]; then
  dispatch=$(curl_api POST "$api/actions/workflows/boda-release.yml/dispatches" '{"ref":"main","return_run_details":true}')
  dispatch_fields=$(printf '%s' "$dispatch" | python3 -c 'import json,sys
m=json.load(sys.stdin)
r=m.get("workflow_run_id")
u=m.get("html_url","")
if not isinstance(r,(int,str)) or not str(r).isdigit(): raise SystemExit("dispatch response missing workflow_run_id")
print(str(r)+"\t"+(u if isinstance(u,str) else ""))') || exit 1
  IFS=$(printf '\t') read -r run_id dispatch_url <<EOF
$dispatch_fields
EOF
  [ -n "$run_id" ] || { echo "dispatch response missing workflow_run_id" >&2; exit 1; }
fi

deadline=$(( $(date +%s) + timeout_seconds ))
metadata=
while :; do
  now=$(date +%s)
  remaining=$(( deadline - now ))
  [ "$remaining" -gt 0 ] || { echo "timed out waiting for workflow run" >&2; exit 1; }
  request_max=$request_timeout_seconds
  [ "$request_max" -le "$remaining" ] || request_max=$remaining
  metadata=$(curl_api GET "$api/actions/runs/$run_id" "" "$request_max") || exit 1
  now=$(date +%s)
  [ "$now" -le "$deadline" ] || { echo "timed out waiting for workflow run" >&2; exit 1; }
  state=$(printf '%s' "$metadata" | python3 -c 'import json,sys
m=json.load(sys.stdin)
print(str(m.get("status", ""))+"\t"+str(m.get("conclusion", "")))') || exit 1
  IFS=$(printf '\t') read -r run_status run_conclusion <<EOF
$state
EOF
  [ "$run_status" = completed ] && break
  remaining=$(( deadline - now ))
  [ "$remaining" -gt 0 ] || { echo "timed out waiting for workflow run" >&2; exit 1; }
  sleep_for=$poll_seconds
  [ "$sleep_for" -le "$remaining" ] || sleep_for=$remaining
  [ "$sleep_for" -eq 0 ] || sleep "$sleep_for"
done

meta_fields=$(printf '%s' "$metadata" | python3 -c 'import json,sys
m=json.load(sys.stdin)
for key in ("path","event","head_branch","head_sha","html_url","status","conclusion"):
 v=m.get(key,"")
 if not isinstance(v,str): v=str(v)
 print(v.replace("\\","\\\\").replace("\t"," ").replace("\n"," "),end="\t")
print()')
IFS=$(printf '\t') read -r workflow_path workflow_event head_branch head_sha run_url run_status run_conclusion <<EOF
$meta_fields
EOF
[ "$workflow_path" = ".github/workflows/boda-release.yml" ] || { echo "refusing unexpected workflow path: $workflow_path" >&2; exit 1; }
[ "$workflow_event" = "workflow_dispatch" ] || { echo "refusing non-manual workflow event: $workflow_event" >&2; exit 1; }
[ "$head_branch" = "main" ] || { echo "refusing workflow run not on main: $head_branch" >&2; exit 1; }
[ "$run_status" = completed ] || { echo "refusing incomplete workflow run: $run_status" >&2; exit 1; }
[ "$run_conclusion" = success ] || { echo "refusing unsuccessful workflow run: $run_conclusion" >&2; exit 1; }
[ "${#head_sha}" -eq 40 ] || { echo "refusing invalid workflow head SHA" >&2; exit 1; }
case "$head_sha" in *[!0-9a-fA-F]*) echo "refusing invalid workflow head SHA" >&2; exit 1;; esac
[ -n "$run_url" ] || { echo "workflow run has no URL" >&2; exit 1; }

work_tmp=$(mktemp -d "${TMPDIR:-/tmp}/boda-release.XXXXXX")
worktree=$work_tmp/worktree
artifact=$work_tmp/artifact
zip_file=$work_tmp/artifact.zip
venv=$work_tmp/venv
clone_dir=
askpass=$work_tmp/askpass
cleanup() {
  if [ -n "${worktree:-}" ] && [ -d "$worktree" ] && [ -n "${repo:-}" ]; then git -C "$repo" worktree remove --force "$worktree" >/dev/null 2>&1 || true; fi
  if [ -n "${work_tmp:-}" ] && [ -d "$work_tmp" ]; then rm -rf "$work_tmp"; fi
}
trap cleanup EXIT HUP INT TERM
mkdir -p "$artifact"

artifact_url=$(curl_api GET "$api/actions/runs/$run_id/artifacts?per_page=100" | python3 -c 'import json,sys
m=json.load(sys.stdin)
want="boda-site-"+sys.argv[1]
for a in m.get("artifacts",[]):
 if a.get("name")==want and a.get("expired") is False and isinstance(a.get("archive_download_url"),str): print(a["archive_download_url"]); break
else: raise SystemExit("no unexpired exact release artifact")' "$head_sha") || exit 1
[ -n "$artifact_url" ] || { echo "no unexpired exact release artifact" >&2; exit 1; }
printf 'Authorization: Bearer %s\n' "$token" | curl --fail --silent --show-error --location --connect-timeout 15 --max-time "$request_timeout_seconds" --header @- --header 'Accept: application/vnd.github+json' --output "$zip_file" "$artifact_url"
python3 -c 'import pathlib,sys,zipfile
root=pathlib.Path(sys.argv[2]).resolve()
with zipfile.ZipFile(sys.argv[1]) as z:
 for n in z.namelist():
  p=(root/n).resolve()
  if p!=root and root not in p.parents: raise SystemExit("artifact contains unsafe path")
 z.extractall(root)' "$zip_file" "$artifact"
[ -f "$artifact/BODACLI_BUILD.json" ] || { echo "artifact missing BODACLI_BUILD.json" >&2; exit 1; }
[ -f "$artifact/SHA256SUMS" ] || { echo "artifact missing SHA256SUMS" >&2; exit 1; }
artifact_sha=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("commit", ""))' "$artifact/BODACLI_BUILD.json")
[ "$artifact_sha" = "$head_sha" ] || { echo "artifact commit does not match workflow head SHA" >&2; exit 1; }

cat >"$askpass" <<'ASKPASS'
#!/bin/sh
case "${1:-}" in
  *Username*) printf 'x-access-token\n' ;;
  *) printf '%s\n' "${GITHUB_TOKEN:-${GH_TOKEN:-}}" ;;
esac
ASKPASS

git_authenticated() (
  unset BODA_ENV_FILE BODA_SESSION_FILE BODA_IAAA_USERNAME BODA_IAAA_PASSWORD BODA_IAAA_OTP
  GIT_ASKPASS="$askpass" GIT_TERMINAL_PROMPT=0 git -c credential.helper= "$@"
)

git_materialize() (
  unset BODA_ENV_FILE BODA_SESSION_FILE BODA_IAAA_USERNAME BODA_IAAA_PASSWORD BODA_IAAA_OTP
  git -c core.hooksPath=/dev/null "$@"
)
chmod 700 "$askpass"

repo=
repo_root=$(git -C "$PWD" rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$repo_root" ]; then
  origin=$(git -C "$repo_root" remote get-url origin 2>/dev/null || true)
  case "$origin" in
    https://github.com/scope-pku/scope-pku.github.io.git|https://github.com/scope-pku/scope-pku.github.io|git@github.com:scope-pku/scope-pku.github.io.git|ssh://git@github.com/scope-pku/scope-pku.github.io.git)
      repo=$repo_root
      git_authenticated -C "$repo" fetch --no-tags https://github.com/scope-pku/scope-pku.github.io.git "$head_sha"
      token=
      unset GITHUB_TOKEN GH_TOKEN
      git_materialize -C "$repo" worktree add --detach "$worktree" "$head_sha";;
  esac
fi
if [ -z "$repo" ]; then
  clone_dir=$worktree
  git_authenticated -c core.hooksPath=/dev/null clone --filter=blob:none --no-checkout https://github.com/scope-pku/scope-pku.github.io.git "$clone_dir"
  token=
  unset GITHUB_TOKEN GH_TOKEN
  git_materialize -C "$clone_dir" sparse-checkout set boda_release
  git_materialize -C "$clone_dir" checkout --detach "$head_sha"
fi
env_source=${BODA_ENV_FILE:-}
[ -n "$env_source" ] && [ -f "$env_source" ] || env_source=
if [ -z "$env_source" ] && [ -n "${repo_root:-}" ] && [ -f "$repo_root/.env" ]; then env_source=$repo_root/.env; fi
if [ -z "$env_source" ] && [ -f "$PWD/.env" ]; then env_source=$PWD/.env; fi
python3 -m venv "$venv"
(
  unset BODA_ENV_FILE BODA_SESSION_FILE BODA_IAAA_USERNAME BODA_IAAA_PASSWORD BODA_IAAA_OTP
  "$venv/bin/python" -m pip install --disable-pip-version-check -r "$worktree/boda_release/requirements.txt"
)
if [ -n "$env_source" ]; then cp "$env_source" "$worktree/.env"; chmod 600 "$worktree/.env"; fi
cli_python=$venv/bin/python

printf 'run=%s\nsha=%s\nmode=%s\npath=/new\n' "$run_url" "$head_sha" "$mode"
export BODA_PATH_PREFIX=/new
(cd "$worktree" && "$cli_python" -m boda_release plan "$artifact")
if [ "$plan_only" = false ]; then
  (cd "$worktree" && "$cli_python" -m boda_release probe --path-prefix /new)
  if [ "$probe_only" = false ]; then
    expected=DEPLOY_NONATOMIC; [ "$mode" = incremental ] && expected=DEPLOY_INCREMENTAL
    if [ -z "$confirm" ]; then
      [ -r /dev/tty ] || { echo "deployment confirmation requires /dev/tty or --confirm" >&2; exit 2; }
      printf 'Type %s to deploy to /new: ' "$expected" >/dev/tty
      IFS= read -r confirm </dev/tty
    fi
    [ "$confirm" = "$expected" ] || { echo "invalid deployment confirmation" >&2; exit 2; }
    if [ "$mode" = incremental ]; then
      (cd "$worktree" && "$cli_python" -m boda_release deploy "$artifact" --incremental --path-prefix /new --apply --confirm "$confirm")
    else
      (cd "$worktree" && "$cli_python" -m boda_release deploy "$artifact" --path-prefix /new --apply --confirm "$confirm")
    fi
  fi
fi
