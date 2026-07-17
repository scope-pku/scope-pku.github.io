# Xu Group Web

Hugo source for the Xu Group website, with a small Boda V12 client for static
release operations.

## Repository layout

- `site/` — Hugo site source, bilingual content, layouts, assets, and generated
  `public/` output.
- `boda_release/` — the Python Boda client and its dependency list.
- `tools/bodacli` — the formal Boda CLI entry point.
- `tools/build_boda_release.sh` — builds a checked release under
  `dist/boda-site/`.
- `tools/deploy_github_release.sh` — triggers/downloads a GitHub release package and deploys it locally with the matching CLI commit.
- An optional local `source/xulm.pku.edu.cn/` may hold the immutable HTML reference snapshot. It is intentionally excluded from Git and must not be edited when present.
- `AGENTS.md` and [`BODA_DEPLOYMENT.md`](BODA_DEPLOYMENT.md) — project rules and
  deployment/rollback details.

## Hugo preview and build

Install Hugo, then run from `site/`:

```sh
hugo server   # local preview
hugo          # production build into site/public/
```

Keep Chinese and English pages equivalent in meaning. See
[`site/README.md`](site/README.md) for content conventions.

## GitHub Pages

Every push to `main` deploys the Hugo site to <https://scope-pku.github.io/> through `.github/workflows/pages.yml`; manual runs remain available through `workflow_dispatch`. The repository's Pages source is configured as **GitHub Actions**; the workflow obtains the public base URL from `actions/configure-pages`, builds `site/`, and deploys the generated artifact without committing `site/public/`.

The Pages source must be enabled once in **Settings → Pages → Build and deployment → GitHub Actions**, or through the GitHub CLI/API before the first workflow run. It is already enabled for `scope-pku/scope-pku.github.io`.

## Boda CLI

Install the Python dependencies from the repository root:

```sh
python3 -m pip install -r boda_release/requirements.txt
```

The CLI reads `BODA_IAAA_USERNAME`, `BODA_IAAA_PASSWORD`, and optional
`BODA_IAAA_OTP` from the environment or root `.env`; never commit those
credentials. Sessions are automatically stored and reused in the user cache:
`~/Library/Caches/bodacli/session.cookies` on macOS, `<XDG_CACHE_HOME>/bodacli/session.cookies`
when `XDG_CACHE_HOME` is set, or `~/.cache/bodacli/session.cookies` on other
systems. `BODA_SESSION_FILE` is an advanced override. The client creates the
cache directory and keeps the session file at mode `0600`; keep `.env` at mode
`0600` too. `BODA_IAAA_OTP` may be a Base32 seed, an `otpauth://` URI, or a
current six-digit code.

Build and inspect a release:

```sh
tools/build_boda_release.sh
tools/bodacli plan dist/boda-site
tools/bodacli probe
```

For the public repository's fixed `/new` package workflow, export a local `GITHUB_TOKEN` with Actions read/write and Contents read permission. Download the deploy tool completely before running it; this avoids executing an empty or partial response if GitHub authentication or the network fails:

```sh
deploy_script=$(mktemp)
chmod 600 "$deploy_script"
trap 'rm -f "$deploy_script"' 0 HUP INT TERM
printf 'Authorization: Bearer %s\n' "$GITHUB_TOKEN" \
  | curl -fsSL --connect-timeout 15 --max-time 300 --header @- --header 'Accept: application/vnd.github.raw+json' \
      --output "$deploy_script" \
      https://api.github.com/repos/scope-pku/scope-pku.github.io/contents/tools/deploy_github_release.sh \
  && sh "$deploy_script"
```

The tool uses GitHub REST directly—`gh` is not required. It triggers/downloads the package, checks out its exact CLI commit, creates a temporary virtual environment, runs plan/probe, and requests the `/new` deployment confirmation. Run `sh "$deploy_script" --plan-only` for a read-only package check. GitHub Actions stores no Boda credentials and does not contact Boda; see [`docs/operator-guide.md`](docs/operator-guide.md) for token permissions, all options, and approval requirements.

`probe` is read-only. A CRUD smoke test is an explicitly destructive,
immediate production write at `/test/A/B.txt`; run the fixed wrapper directly,
never concurrently:

Deploy only an approved release, with the explicit confirmation:

```sh
tools/bodacli deploy dist/boda-site --apply --confirm DEPLOY_NONATOMIC
```

For a complete local Hugo build followed by manifest-based synchronization, use incremental deploy:

```sh
tools/bodacli deploy dist/boda-site --incremental --apply --confirm DEPLOY_INCREMENTAL
```

All deployment modes require the current Git worktree to be clean. Incremental mode compares the SHA-256 manifest of the complete `dist/boda-site/` output. The builder writes local `BODACLI_BUILD.json` provenance; it is not uploaded, and deploy refuses an artifact whose recorded commit/dirty state differs from the current worktree. Hugo fan-out means one source change can affect many generated files; `git diff` is only for commit ancestry and source-change audit, never a direct source-to-output upload map. With no `bodacli-state.txt`, incremental deploy performs a full bootstrap. The public state file contains canonical JSON metadata only: schema, commit, dirty flag, path prefix, and generated-file SHA-256 entries—never source or credentials. Invalid, mismatched, dirty-baseline, non-ancestor, or remotely drifted state fails closed. It deletes only old-state files whose recorded checksum still matches, never directories, verifies public deletion with cache-busting requests, and writes state last. Both full and incremental deploys are non-atomic; ordinary full deploy continues to use `DEPLOY_NONATOMIC`.

The client uses the English default security reason `Published by bodacli at
<UTC ISO timestamp>.`; set optional `BODA_SECURITY_REASON` only when a custom
audit explanation is needed.

Set `BODA_PATH_PREFIX` (and, when needed, `BODA_BASE_URL` or `BODA_PUBLIC_URL`)
to target a configured path. Uploads become public immediately; an unlinked
path is not access control. Do not upload secrets or unfinished private
material. New uploads with structured receipts record the Boda file-security
review. Existing-file overwrites may instead return the exact body `ok`; the
client accepts only that receiptless response and verifies the public checksum.
The CRUD test may additionally confirm its known `B.txt` by directory listing.

## Documentation

- [`docs/README.md`](docs/README.md) — documentation index and reading paths.
- [`docs/developer-guide.md`](docs/developer-guide.md) — developer guide.
- [`docs/operator-guide.md`](docs/operator-guide.md) — operator guide.
