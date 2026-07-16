# Boda deployment and rollback runbook

## Confirmed platform behavior

- Static uploads become public immediately; do not use the global `发布` action
  during a static deployment probe.
- `批量上传文件` uses an HTML5 multi-file input, but it does not preserve a
  selected directory tree. The current Hugo build spans 49 directories, so a
  UI-only deployment requires one directory at a time.
- A Boda website package is a platform backup containing CMS data, templates,
  files, and metadata. A Hugo ZIP is not a website package and must not be
  imported as one.
- Importing a website package overwrites the current site and clears the
  full-text search index. The index must be rebuilt after a restore.
- The bare domain currently serves `/index.htm`; `/index.html` returns 404.
  The release builder therefore replaces Hugo's root alias with the real home
  page at both names.

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

The verified output is written to ignored `dist/boda-site/`. It contains a
checksum manifest and fails if development URLs, VSB references, or filenames
rejected by Boda are found.

GitHub Actions runs the same builder for every pull request and push to `main`.
Pull requests only validate the build; `main` and manual runs retain the release
artifact for three days. CI does not upload files to Boda or publish the site.

## Recommended production operation

1. Freeze and tag the approved Git commit, then build from that tag.
2. Verify the rollback package and its off-machine copy.
3. Request a supported directory-level static upload or server-side sync from
   the Boda administrator. This is preferable to 49 manual directory uploads.
4. If no directory-level channel exists, create missing directories and use
   Boda multi-file upload once per directory. Upload assets first, then nested
   pages, then legacy aliases, and upload root `index.htm` last.
5. Do not delete old CMS templates or unrelated assets during the first cutover.
   Do not click global `发布`, because CMS publishing may regenerate old pages.
6. Test the root, `/zh/`, representative sections, PDFs, language switches,
   legacy `.htm` URLs, HTTPS, mobile layouts, and cache-busting query URLs.
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
