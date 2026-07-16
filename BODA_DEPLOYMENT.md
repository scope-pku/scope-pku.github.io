# Boda deployment and rollback runbook

## Confirmed platform behavior

- Static uploads become public immediately; do not use the global `发布` action
  during a static deployment probe.
- `批量上传文件` uses an HTML5 multi-file input, but it does not preserve a
  selected directory tree. The lowercase-only Hugo build spans 46 directories,
  so a
  UI-only deployment requires one directory at a time.
- A Boda website package is a platform backup containing CMS data, templates,
  files, and metadata. A Hugo ZIP is not a website package and must not be
  imported as one.
- Importing a website package overwrites the current site and clears the
  full-text search index. The index must be rebuilt after a restore.
- Apache prefers `index.htm` over `index.html` when both exist. The release
  builder therefore makes them identical so a directory URL cannot select a
  redirect file instead of the real home page.
- Boda prepends a UTF-8 BOM to uploaded CSS and JavaScript. That changes their
  bytes and breaks Hugo's subresource-integrity hashes, so the release builder
  removes `integrity` attributes from generated HTML before deployment.

## Local rollback material

The Boda package created at 2026-07-16 13:49 predates the Hugo probe and passed
Boda's `全检通过` validation. Local copies are stored under the ignored path:

`backups/boda/2026-07-16/`

The directory contains the 88 MB `.vsbsitepackage`, its 272 MB `.sto` companion,
and `SHA256SUMS`. Copy this directory to a second storage location before
production deployment. The HTML-only snapshot in `source/xulm.pku.edu.cn/` is
useful for comparison but is not a complete CMS rollback.

These archives contain Boda-specific ZIP metadata that generic archive tools
may warn about. Do not unpack and repack them; retain the original bytes and
use Boda's `全检通过` result plus the recorded SHA-256 values for validation.

## Build the release candidate

Run from the repository root:

```sh
tools/build_boda_release.sh
```

Set `BODA_PATH_PREFIX` to deploy the same site below a directory. Empty or `/`
targets the site root; `/new` targets `/new/`; nested values such as
`/trial/site` are also supported. The builder, uploader target, and public
checksum verification all use this single value.

The verified output is written to ignored `dist/boda-site/`. It contains a
checksum manifest and fails if development URLs, VSB references, or filenames
rejected by Boda are found.

GitHub Actions runs the same builder for manual runs on `main` and retains the release artifact for three days. The default `plan` operation is read-only; `probe` checks the configured Boda session. `deploy` performs a full immediate remote write only after the `DEPLOY_NONATOMIC` confirmation, while `incremental` performs manifest-based synchronization only after `DEPLOY_INCREMENTAL`. Both write modes are non-atomic.
The workflow authenticates through IAAA using repository secrets
`BODA_IAAA_USERNAME`, `BODA_IAAA_PASSWORD`, and the optional Base32 TOTP seed
`BODA_IAAA_OTP`. The client automatically stores and reuses the session in the
user cache: `~/Library/Caches/bodacli/session.cookies` on macOS,
`<XDG_CACHE_HOME>/bodacli/session.cookies` when `XDG_CACHE_HOME` is set, or
`~/.cache/bodacli/session.cookies` on other systems. `BODA_SESSION_FILE` is an
advanced override. The client creates the cache directory and keeps the session
file at mode `0600`; keep `.env` at mode `0600` too. Within a GitHub Actions job,
steps may reuse the runner's cache file, but a new runner/workflow run does not
inherit a previous run's local cache. None of these values belongs in Git.
The default security reason is the English `Published by bodacli at <UTC ISO
timestamp>.`; set optional `BODA_SECURITY_REASON` only when a custom audit
explanation is needed.

The Python client creates missing release directories from shallow to deep, using a fresh CSRF token for each creation. Structured upload receipts are recorded through Boda's file-security check. Existing-file overwrites may return only the exact body `ok`; these have no security fields, so the client requires public checksum verification instead. Full deploy uploads the complete release and does not remove remote files. Incremental deploy may remove only files declared by the previous state whose remote content still matches the recorded checksum; it never removes directories or unrelated files.

## Incremental deployment protocol

Incremental mode still performs a complete local Hugo build before comparing the output manifest. Hugo can fan out one source change into many generated files, so the upload set is the SHA-256 manifest diff of the complete `dist/boda-site/` output, not a list of pages inferred from `git diff`. Git history is used only to verify the commit relationship and audit source changes; it is not a mapping from source files to Hugo output.

The command is:

```sh
tools/bodacli deploy dist/boda-site --incremental --apply --confirm DEPLOY_INCREMENTAL
```

The `bodacli-state.txt` protocol is public canonical JSON metadata stored in a Boda-supported TXT file, not a secret. It contains only the schema version, deployed commit, dirty flag, path prefix, and the generated-file SHA-256 manifest. It contains no source, credentials, cookies, or other secrets. The builder also writes local `BODACLI_BUILD.json` provenance; it is excluded from `SHA256SUMS` and upload, and deploy rejects an artifact whose recorded commit/dirty state differs from the current worktree. Incremental deployment requires the current Git worktree to be clean. A first incremental deploy with no state performs a full bootstrap. A state that is malformed, has a different path prefix, points to a non-ancestor commit, records a dirty tree as its baseline, or detects remote content drift fails closed without uploading or deleting.

Deletion is bounded: only paths declared by the old state and still matching its checksum may be deleted; directories are never deleted automatically. Each deletion must disappear from both the authenticated management listing and a cache-busted public URL before the state file is written last. The client re-reads state before writes and before publication, but Boda exposes no atomic compare-and-swap, so manual deployments must never overlap; GitHub Actions concurrency serializes workflow runs. Both full and incremental deployments are non-atomic: a failure can leave a mixed remote version and must be handled as a partial deployment.

Ordinary full deploy continues to use `DEPLOY_NONATOMIC`, but all deployments require a clean worktree and matching `BODACLI_BUILD.json`; dirty artifacts are rejected before remote writes.

## Recommended production operation

1. Freeze and tag the approved Git commit, then build from that tag.
2. Verify the rollback package and its off-machine copy.
3. Request a supported directory-level static upload or server-side sync from
   the Boda administrator. This is preferable to 49 manual directory uploads.
4. If no directory-level channel exists, create missing directories and use
   Boda multi-file upload once per directory. Upload assets first, then nested
   lowercase pages, and upload root `index.htm` last.
5. Do not delete old CMS templates or unrelated assets during the first cutover.
   Do not click global `发布`, because CMS publishing may regenerate old pages.
6. Test the root, `/zh/`, representative lowercase sections, PDFs, language
   switches, HTTPS, mobile layouts, and cache-busting query URLs.
7. Remove stale files only in a later maintenance pass after the new site has
   remained stable and the rollback path has been rehearsed.

## Rollback operation

1. Open `管理中心` → `备份恢复` → `导入导出网站包`.
2. Upload and select `xulimei_all_260716.vsbsitepackage`.
3. Confirm the destructive import only after the new-site failure has been
   recorded and the rollback decision maker approves it.
4. Rebuild the full-text search index as required by Boda.
5. Confirm whether a global publish is required to regenerate the restored
   public pages, then verify `/`, `/index.htm`, core sections, and assets.
