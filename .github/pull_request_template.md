## Summary

<!-- What changed, and why? Link the related issue if there is one. -->

## Validation

<!-- List the commands you actually ran and their results. -->

```text
- [ ] hugo --source site --minify
- [ ] uv run pytest tests (when Python or deployment tooling changed)
```

## Screenshots

<!-- Include desktop and mobile screenshots for user-visible changes, or write N/A. -->

## Risk and follow-up

<!-- Mention URL, bilingual content, dependency, data, deployment, or compatibility impact. -->

## PR checklist

- [ ] This PR has one focused purpose and links the related issue, if applicable.
- [ ] I read `AGENTS.md` and the relevant development, content, or operator guide.
- [ ] I did not modify `source/xulm.pku.edu.cn/` or commit generated `site/public/` output.
- [ ] English and Chinese content remain equivalent in facts, claims, caveats, links, people, and dates.
- [ ] Paired bilingual pages use the same relative path and `translationKey`.
- [ ] I did not invent or strengthen scientific, biographical, award, date, method, or result claims.
- [ ] User-visible changes follow `DESIGN.md`; desktop and mobile layouts were checked.
- [ ] New or changed images have accurate alt text and interactive controls remain keyboard accessible.
- [ ] `hugo --source site --minify` passes.
- [ ] `uv run pytest tests` passes when Python or deployment tooling changed.
- [ ] Actual validation commands and results are listed above.
- [ ] URL, dependency, configuration, data, or compatibility changes are documented above.
- [ ] No credentials, OTPs, cookies, `.env` files, private material, or unrelated generated files are included.
- [ ] I did not manually deploy GitHub Pages or perform an unauthorized Boda upload, CRUD smoke test, or production deployment.
- [ ] Related documentation was updated when commands, paths, or workflow behavior changed.

<!-- Keep each item and write N/A with a reason when it does not apply. -->
