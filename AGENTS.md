# Xu Group Web

## Scope

- Rebuild the Xu Group website with Chinese and English content.
- `source/xulm.pku.edu.cn/` is a read-only snapshot of public HTML fetched from
  `https://xulm.pku.edu.cn/index.htm` on 2026-07-15. Preserve its paths and do
  not edit it when building the replacement site.
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
  with the immutable source and edit its content, semantics, captions, and
  layout deliberately by hand.

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
- Apache resolves an uploaded `index.html` as the directory index, and both
  HTTP and HTTPS served the probe with the original HTML and executable inline
  JavaScript intact. Public responses currently use a 600-second cache.
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
  CSS/JS/media, and legacy `.htm` aliases.
- Upload only a clean production Hugo build, never Hugo source directories.
  `hugo server` output can contain `livereload.js` and localhost canonical
  URLs, so regenerate with plain `hugo` before deployment.
- Do not publish or replace the existing site merely to test static-file
  storage. Confirm the isolated path through preview or a direct URL first.
