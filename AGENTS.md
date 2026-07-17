# Xu Group Web

## Scope

- Rebuild the Xu Group website with Chinese and English content.
- A local `source/xulm.pku.edu.cn/` may contain the read-only public HTML snapshot fetched from `https://xulm.pku.edu.cn/index.htm` on 2026-07-15. It is intentionally excluded from Git; when present, preserve its paths and do not edit it when building the replacement site.
- `site/` contains the Hugo replacement. Run Hugo commands from that directory.
- `DESIGN.md` is the visual and editorial source of truth. Read it before
  changing layouts, styles, components, or public-facing copy.

## Working rules

- Keep Chinese and English content equivalent in meaning; do not infer scientific
  claims or biographical details that are absent from approved source material.
- Preserve existing public URLs where practical, and record intentional URL
  changes before publishing.
- Do not add dependencies unless the existing project cannot meet the need.
- Keep patches small and verify changed pages locally before handoff.
- `tools/migrate_english.py` is retained only as a record of the initial bulk
  bootstrap. Do not run it during page-by-page optimization. Compare each page
  with the optional local immutable snapshot when available, and edit each page's content, semantics, captions, and layout deliberately by hand.
- Python tests live only under `tests/` and are maintained with `pytest`; run `python3 -m pytest tests` from the repository root. Verify the Hugo website with Hugo builds, browser checks, link checks, and other web-appropriate tools rather than forcing page validation into pytest.

## Boda CMS deployment

- The remote platform is Boda V12. The available account currently exposes one
  site, `徐莉梅课题组英文站`; no independent site-creation control has been found.
- Keep deployment probes isolated in an unlinked directory and never click the
  global `发布` action during a probe. The current probe directory is
  `hugoprobe20260716`, titled `Hugo可行性测试未发布`.
- Treat every file upload as an immediate production write: an uploaded
  `index.html` became publicly reachable at
  `https://xulm.pku.edu.cn/<directory>/` without using the global `发布` action.
  An unlinked directory and a title containing `未发布` provide obscurity, not
  access control. Never upload secrets or unfinished private material.
- Apache prefers `index.htm` over `index.html` when both exist. Keep the two
  root entry files identical; a self-redirecting `index.htm` causes an infinite
  refresh loop. Public responses currently use a 600-second cache.
- Boda prepends a UTF-8 BOM to uploaded CSS and JavaScript. This invalidates
  Hugo's subresource-integrity hashes and makes browsers reject those assets,
  so Boda release HTML must not contain `integrity` attributes.
- `BODA_PATH_PREFIX` is the single deployment-path setting. Empty or `/`
  targets the root; `/new` and nested values such as `/trial/site` prefix Hugo
  URLs, the Boda upload root, and public checksum verification together.
- The file manager accepts static assets including HTML, HTM, CSS, JavaScript,
  SVG, images, fonts, XML, and PDF. Its upload page reports a 1000 MB total
  limit and restricts filenames to Chinese, English, digits, `-`, and `_`.
- Boda website-package import overwrites the current site. Export and retain a
  site package before any import or production replacement.
- Boda template history and website packages are rollback aids, not source
  control. Keep Hugo and Git canonical; do not make routine JSP, CSS, or
  JavaScript edits only in Boda.
- No Git, SSH, SFTP, database, web-server configuration, or operating-system
  access has been found in the Boda UI.

### Boda CLI safety rules

- The formal general entry point is `tools/bodacli`; do not document or use a compatibility copy of the old wrapper. Install the client dependencies with `python3 -m pip install -r boda_release/requirements.txt`.
- Authentication values come from environment variables or the repository-root `.env` (`BODA_IAAA_USERNAME`, `BODA_IAAA_PASSWORD`, and optional `BODA_IAAA_OTP`); never commit them. The client automatically stores and reuses the session in the user cache at `~/Library/Caches/bodacli/session.cookies` on macOS, `<XDG_CACHE_HOME>/bodacli/session.cookies` when `XDG_CACHE_HOME` is set, or `~/.cache/bodacli/session.cookies` on other systems. `BODA_SESSION_FILE` is an advanced override. The client creates the cache directory and keeps the session file at mode `0600`; keep `.env` at mode `0600` too.
- Deployments use the English default security reason `Published by bodacli at <UTC ISO timestamp>.`; set optional `BODA_SECURITY_REASON` only when a custom audit explanation is needed.
- `BODA_IAAA_OTP` accepts a Base32 seed, an `otpauth://` URI, or an already-generated six-digit one-time code.
- `tools/boda_crud_test.sh` performs immediate production writes at `/test/A/B.txt`, then deletes the file and directory. It refuses to run if `A` already exists; never run it concurrently with another CRUD test or deployment.
- New uploads may return a structured security receipt, while overwriting an existing file may return the exact plain-text body `ok`. Deployment may accept only that exact receiptless overwrite and must then verify the public checksum; structured receipts still require the Boda file-security update. The CRUD test may additionally confirm its known `B.txt` through a fresh directory listing.
- `.github/workflows/boda-release.yml` may only build and retain the fixed `/new` release artifact. GitHub-hosted runners cannot complete the Boda CAS handoff; do not store Boda credentials in GitHub Secrets or restore remote upload steps. Use `tools/deploy_github_release.sh` locally so the artifact is deployed with the CLI from its exact Git commit.
- GitHub concurrency serializes package creation only and is not a deployment lock. Never overlap local full or incremental deploy processes.

### Boda browser pitfalls

- CAS login token URLs are effectively one-use. Reloading a consumed
  `caslogin.jsp?...token=...` page can return to IAAA and discard the working
  frameset session.
- Boda uses deeply nested legacy frames. A click may report success without
  changing the target frame. Verify navigation from the target frame's hidden
  `position` value and visible file list, not from the click result.
- The read-only folder URL
  `/system/site/foldercontent.jsp?position=FOLD:<path>&folder_name=` is useful
  for confirming a directory and its contents.
- Directly opened dialog pages such as `newfolder.jsp` and `newfile.jsp` lack
  parent functions including `top.showDialog` or `top.closeDialog`. A form may
  still submit despite the resulting JavaScript error, so check remote state
  before retrying and creating duplicates.
- The in-app Browser cannot select a local file in the native macOS file
  chooser. Prepare and verify the local artifact first, then ask the user for
  the single file-selection step; resume automation only after the upload page
  visibly lists the chosen file.
- Never claim that a local artifact exists from an edit-tool success alone.
  Confirm it with `test -f`, `ls`, and a non-zero size before handing its path
  to the user.

### Hugo compatibility probe

- Probe the smallest useful artifact first: one self-contained `index.html`
  with an unmistakable marker and inline CSS/JavaScript. Only after it is
  served correctly should the probe add nested `index.html` pages, independent
  CSS/JS/media, and lowercase content routes.
- Upload only a clean production Hugo build, never Hugo source directories.
  `hugo server` output can contain `livereload.js` and localhost canonical
  URLs, so regenerate with plain `hugo` before deployment.
- Do not publish or replace the existing site merely to test static-file
  storage. Confirm the isolated path through preview or a direct URL first.

### Incremental deployment protocol

- Every incremental deployment performs a complete local Hugo build. Select uploads from the SHA-256 manifest diff of the complete `dist/boda-site/` output; Hugo fan-out means `git diff` must not be treated as a source-to-output map. Use Git only for commit ancestry checks and source-change audit. The builder writes local `BODACLI_BUILD.json` provenance, which is excluded from upload; deploy must reject a release whose recorded commit/dirty state differs from the current worktree.
- Invoke incremental deploy as `tools/bodacli deploy dist/boda-site --incremental --apply --confirm DEPLOY_INCREMENTAL`. A missing state bootstraps with a full deploy. `bodacli-state.txt` is a publicly served TXT file containing canonical JSON metadata only: schema, commit, dirty flag, path prefix, and generated-file SHA-256 entries; it must contain no source or credentials.
- Incremental deployment requires a clean current Git worktree. State validation is fail-closed for corruption, path-prefix mismatch, non-ancestor commit, dirty baseline, remote checksum drift, or a state change detected during the operation. Delete only files declared by the old state whose remote checksum still matches; never delete directories. Confirm each deletion through the management listing and a cache-busted public 404 before writing state last. The server has no atomic compare-and-swap, so manual deployments must never overlap; GitHub Actions concurrency covers workflow runs. Full and incremental deploys are non-atomic.
- Ordinary full deploy keeps `DEPLOY_NONATOMIC`, but all deployments require a clean worktree and matching `BODACLI_BUILD.json`; a dirty artifact must never be uploaded.
