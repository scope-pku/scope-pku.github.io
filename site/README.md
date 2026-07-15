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

## Refresh the English migration

Run `python3 tools/migrate_english.py` from the repository root to rebuild the
English Markdown, data files, and local media from the read-only HTML snapshot.
The migration keeps source spellings and claims, removes two exact duplicate
news items, and excludes the previous VSB scripts and styles.

## Existing URLs

English remains the default language at the site root, matching the previous
website, while Chinese pages use `/zh/`. The English section files define
aliases for the previous public `.htm` URLs. Keep these aliases when migrating
content so existing links redirect to the corresponding replacement section.
