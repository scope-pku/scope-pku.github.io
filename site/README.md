# Xu Group Hugo site

## Preview

Install Hugo, then run:

```sh
cd site
hugo server
```

Open the local address printed by Hugo. Chinese pages live under `content/zh/`
and English pages under `content/en/`.

## Add paired content

Create one Markdown file in each language using the same relative path and the
same `translationKey`. Keep the two files equivalent in meaning. Set
`draft: false` when the page is ready to publish.

The generated static website is written to `site/public/` by `hugo`.

## Historical English migration

`tools/migrate_english.py` records the initial bulk bootstrap from the read-only
HTML snapshot. Do not run it against the maintained site: it rewrites English
Markdown, data files, and local media. Compare individual pages with the
immutable source and edit them deliberately instead.

## Existing URLs

English remains the default language at the site root, matching the previous
website, while Chinese pages use `/zh/`. All maintained routes and directories
use lowercase names. The replacement site does not generate legacy aliases.
