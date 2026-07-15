# Xu Group Website Page-by-Page Optimization

This checklist tracks the English redesign first. Shared templates must remain
compatible with the existing Chinese placeholders; Chinese content parity begins
only after the English design is approved.

## Status rule

- Keep an item unchecked while it is being designed, implemented, reviewed, or
  corrected.
- Mark an item complete only after its route passes the page-level definition of
  done below.
- Preserve `source/xulm.pku.edu.cn/` as the immutable comparison source.
- Do not run `tools/migrate_english.py` during optimization; refine every page
  manually against its source and rendered output.

## Definition of done for every page

- Compare the archived/live original and current Hugo page at desktop and
  390 px mobile widths.
- Preserve approved facts, links, image roles, record counts, and cautious
  scientific wording.
- Match the agreed visual direction: modernized PKU identity, editorial
  academic layout, natural scientific imagery, and no legacy CMS defects.
- Verify headings, alt text, keyboard focus, WCAG AA contrast, and no
  document-level horizontal overflow.
- Verify the page route and its legacy alias where one exists.
- Run a clean Hugo build and check that no VSB resources remain.
- Record the completed page in a focused Git commit.

## 0. Planning and shared foundation

- [x] Inventory the original pages, current Hugo routes, reusable templates, and
  page-specific gaps.
- [x] Approve the implementation direction: modernized preservation of the old
  site's PKU identity, English first, page-by-page review.
- [x] Create this persistent page-by-page checklist.
- [x] Rebuild the shared masthead, navigation, breadcrumbs, footer, typography,
  spacing, and canonical contact data before page-specific work.
- [x] Verify shared desktop/mobile navigation, `🌐 CN` / `🌐 EN`, focus states,
  and all 21 legacy aliases.

## 1. Home and research

- [x] **Home** `/` — compare `source/xulm.pku.edu.cn/index.htm`; restore the
  strong PKU masthead and wide group-photo viewpoint, then refine research
  identity, interests, highlights, and recent news without a carousel.
- [x] **Research** `/research/` — compare `Research.htm`; create a dedicated
  reading layout with known figures, captions, references, caveats, and wider
  evidence images.

## 2. People

- [x] **People index** `/people/` — compare `People.htm`; optimize Group Leader,
  current member, and alumni hierarchy while preserving all 29 records.
- [x] **Limei Xu profile** `/people/limei-xu/` — compare
  `info/1011/1012.htm`; present verified role, affiliation, contact links, and CV
  through the canonical contact data.

## 3. News

- [x] **Breaking News** `/news/` — compare `News/Breaking_News.htm`; render all
  43 records as semantic date-and-text editorial rows.
- [x] **All News and Events** `/news/all-news/` — compare
  `News/All_News_and_Events.htm`; preserve all 70 deduplicated records with clear
  year and category rhythm.

## 4. Publications

- [x] **Publications index** `/publications/` — create a clear entry point for
  highlights, the full list, and theses.
- [x] **Research Highlights** `/publications/highlights/` — compare
  `Publications/Highlights.htm`; preserve 15 image-led records, complete titles,
  evidence text, and source links.
- [x] **Full Publication List** `/publications/full-list/` — compare
  `Publications/Full_List.htm`; preserve all 86 citations and author order in
  readable newest-first year groups.
- [x] **Theses** `/publications/theses/` — compare
  `Publications/Theses.htm`; present all 14 bilingual thesis records in a compact
  semantic list rather than repeated tables.

## 5. Teaching

- [x] **Teaching index** `/teaching/` — compare `Teaching.htm`; establish stable
  course fields and visible year navigation.
- [x] **Teaching 2022** `/teaching/2022/` — compare `Teaching/a2022.htm`.
- [x] **Teaching 2021** `/teaching/2021/` — compare `Teaching/a2021.htm`.
- [x] **Teaching 2020** `/teaching/2020/` — compare `Teaching/a2020.htm`.
- [x] **Teaching 2019** `/teaching/2019/` — compare `Teaching/a2019.htm`.

## 6. Photos

- [ ] **Photos index** `/photos/` — create an editorial entry point that
  preserves the role of each gallery.
- [ ] **Group Members** `/photos/group-members/` — compare
  `Photos/Group_Members.htm`; preserve three natural-ratio images.
- [ ] **Meetings** `/photos/meetings/` — compare `Photos/Meetings.htm`; preserve
  two natural-ratio images.
- [ ] **Have Fun** `/photos/have-fun/` — compare `Photos/Have_Fun.htm`; preserve
  three natural-ratio images.
- [ ] **Dine Together** `/photos/dine-together/` — compare the legacy typo route
  `Photos/Dine_Toghter.htm`; preserve its image and alias.
- [ ] **Graduation** `/photos/graduation/` — compare `Photos/Graduation.htm`;
  preserve four natural-ratio images.

## 7. Contact and English release gate

- [ ] **Contact** `/contact/` — compare `Contact_Us.htm`; use the canonical
  address, office, telephone, email, personal page, and student-office details.
- [ ] Run the final English route, content-count, asset, alias, accessibility,
  responsive, and broken-link regression checks.
- [ ] Obtain final English visual approval and tag the English design as locked.

## 8. Chinese parity after English approval

- [ ] Create a second page-by-page Chinese checklist matching every approved
  English route and `translationKey`.
- [ ] Migrate and review Chinese pages without inventing translations, claims,
  biographies, captions, or affiliations.
- [ ] Run bilingual navigation, alternate-language metadata, route parity, and
  production-readiness checks.
