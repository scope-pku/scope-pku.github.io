---
version: alpha
name: PKU Laboratory Notebook
description: An editorial bilingual design system for the SCOPE Group at Peking University.
colors:
  primary: "#8C0000"
  on-primary: "#FFFFFF"
  secondary: "#365F70"
  on-secondary: "#FFFFFF"
  neutral: "#FAF9F6"
  surface: "#FFFFFF"
  on-surface: "#17202A"
  on-surface-variant: "#46515C"
  outline: "#C9C7C2"
  ice: "#DCEBED"
  focus: "#005FCC"
typography:
  display:
    fontFamily: Source Serif 4, Noto Serif SC, Georgia, serif
    fontSize: 64px
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Source Serif 4, Noto Serif SC, Georgia, serif
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Source Serif 4, Noto Serif SC, Georgia, serif
    fontSize: 32px
    fontWeight: 600
    lineHeight: 1.2
  headline-sm:
    fontFamily: Source Serif 4, Noto Serif SC, Georgia, serif
    fontSize: 22px
    fontWeight: 600
    lineHeight: 1.3
  body-lg:
    fontFamily: Inter, Noto Sans SC, PingFang SC, system-ui, sans-serif
    fontSize: 18px
    fontWeight: 400
    lineHeight: 1.65
  body-md:
    fontFamily: Inter, Noto Sans SC, PingFang SC, system-ui, sans-serif
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.65
  body-sm:
    fontFamily: Inter, Noto Sans SC, PingFang SC, system-ui, sans-serif
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: Inter, Noto Sans SC, PingFang SC, system-ui, sans-serif
    fontSize: 13px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: 0.04em
rounded:
  none: 0px
  sm: 2px
  md: 4px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  gutter: 24px
layout:
  contentMax: 1120px
  readingMeasure: 72ch
  columns: 12
motion:
  feedback: 120ms
  content: 180ms
focus:
  color: "{colors.focus}"
  width: 3px
  offset: 3px
components:
  page:
    backgroundColor: "{colors.neutral}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
  masthead-rule:
    backgroundColor: "{colors.primary}"
    height: 6px
  nav-link:
    textColor: "{colors.on-surface}"
    typography: "{typography.label}"
    padding: 8px
  nav-link-active:
    textColor: "{colors.primary}"
    typography: "{typography.label}"
  link:
    textColor: "{colors.primary}"
    typography: "{typography.body-md}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 12px
  research-tag:
    backgroundColor: "{colors.ice}"
    textColor: "{colors.secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: 8px
  metadata:
    textColor: "{colors.on-surface-variant}"
    typography: "{typography.body-sm}"
  content-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.none}"
    padding: 24px
  divider:
    backgroundColor: "{colors.outline}"
    height: 1px
---

# SCOPE Group Design System

## Overview

The website should feel like a **contemporary Peking University laboratory notebook crossed with the opening pages of a peer-reviewed physics journal**. It belongs to an established university research group: precise, calm, cumulative, and confident enough not to advertise itself like a startup.

The primary audiences are research peers, prospective students and postdoctoral researchers, collaborators, current group members, and readers arriving through a paper or news link. They should immediately understand what the group studies, who does the work, and where to find the underlying publications.

The visual system retains the institutional memory of the existing site—Peking University red, the group photograph, and the long-running research archive—while replacing its fixed-width CMS layout with an editorial, responsive structure. Scientific images are evidence and context, not decoration.

### Editorial voice

Use plain, factual, restrained academic prose. Write in the first-person plural when the group is speaking and use third person for individual profiles. Prefer specific methods, systems, evidence, and conditions over promotional adjectives.

- Preserve cautious scientific language such as “may,” “suggests,” “challenging,” and “not well understood.”
- Correct obvious grammar, spacing, capitalization, and typographical errors when scientific meaning is unchanged.
- Do not invent or strengthen claims, affiliations, awards, dates, methods, titles, or outcomes.
- Avoid generic phrases such as “cutting-edge,” “world-leading,” and “state-of-the-art” unless an approved source specifically requires them.
- English uses sentence case. Chinese should read as natural academic Chinese, not a word-for-word translation.

## Colors

The palette uses one institutional accent, one scientific secondary, and quiet paper-like neutrals.

- **PKU red** {colors.primary} is the institutional anchor. Use it for the masthead rule, links, active navigation, and rare emphasis—not for large background fields behind body text.
- **Water blue** {colors.secondary} and **ice tint** {colors.ice} identify research metadata, diagrams, and restrained hover states. They never compete with PKU red for brand ownership.
- **Warm paper** {colors.neutral} is the page ground. It should feel closer to an archival journal page than a software dashboard.
- **White surface** {colors.surface} is reserved for reading areas that need separation from the paper ground.
- **Deep ink** {colors.on-surface} carries headings and body text. Avoid pure black.
- **Slate** {colors.on-surface-variant} carries dates, affiliations, captions, and secondary metadata.
- **Focus blue** {colors.focus} is reserved for keyboard focus because it remains distinct from both brand red and content blue.

All normal text and interactive states must meet WCAG AA contrast. Never encode category or state by color alone.

## Typography

Typography separates the scholarly voice from the navigational interface.

- **Headlines** use a bookish serif stack: Source Serif 4 when locally available, then Noto Serif SC or Georgia. The serif should feel like a journal title, not a luxury brand.
- **Body and interface text** use Inter with Chinese system fallbacks. Long research and publication pages prioritize steady rhythm and legibility.
- **Dates and metadata** use the label or body-small style with tabular numerals where supported.
- Display type is limited to the home title. Interior page titles use headline-large; section headings use headline-medium or headline-small.
- On narrow screens, display and headline sizes scale down with `clamp()` while body text remains at least 16px.

Do not use more than two type families or three weights. Do not set entire navigation bars, headings, or buttons in all caps; a small affiliation eyebrow may use tracked capitals in English.

## Layout

Use a fluid mobile layout and a fixed maximum reading grid on desktop. The outer grid is twelve columns at a maximum width of {layout.contentMax}; long prose stays within {layout.readingMeasure}.

- The header is compact and persistent in structure, not necessarily sticky. A 6px PKU-red rule anchors the page.
- The home hero is asymmetrical: research identity and group image share the first viewport. The image must not push the actual research statement below the fold on a normal laptop.
- Research prose follows a narrow reading column, with figures allowed to extend one or two columns beyond it when useful.
- News and publications use date/metadata columns and horizontal rules, not a grid of interchangeable cards.
- People use a compact portrait-and-facts grid. Current members appear before alumni, and missing fields simply disappear rather than leaving empty labels.
- Photo galleries preserve each image’s natural role and caption; do not crop every photograph into the same aspect ratio when that removes people or scientific detail.
- Mobile pages must never create document-level horizontal scrolling. Navigation may wrap or use an intentionally scrollable row with a visible affordance.

Spacing follows the defined 4/8px rhythm. Section boundaries use 48–64px on desktop and 32–48px on mobile. Related metadata stays close to its heading; unrelated records receive a full rhythm step or a hairline rule.

## Elevation & Depth

The design is materially flat. Hierarchy comes from typography, spacing, hairline rules, and shifts between warm paper and white reading surfaces.

Do not use drop shadows for ordinary cards, navigation, or images. A temporary overlay may use a restrained shadow only when separation cannot be achieved through a border and tonal change. There are no glass layers, gradients, or glowing effects.

## Shapes

The shape language is architectural and nearly square. Most containers have no radius; small controls may use {rounded.sm} or {rounded.md}. Images remain rectangular and align to the grid.

Do not use pill-shaped buttons, badges, or navigation. Circles are reserved for an authentic institutional seal, person portraits that are intentionally circular in source material, or functional status indicators.

## Components

### Masthead and navigation

The masthead combines the group name with a restrained institutional affiliation. If an official PKU mark is used, preserve its proportions and surrounding clear space. Active navigation is indicated by PKU-red text plus an underline or rule, never by a filled pill.

The language switch shows a single approved globe icon followed by the **target** language code: `🌐 EN` on Chinese pages and `🌐 CN` on English pages. Its accessible name spells out the action. This is the only decorative-style Unicode symbol permitted in the header.

### Home hero

The home page opens with the group name, a one-sentence research identity, three concise research interests, and a current group photograph. Avoid a marketing slogan, CTA cluster, carousel, or full-screen splash.

### Research and highlights

Research sections follow: **question or phenomenon → approach → evidence or present understanding → limits and open direction → linked references**. Use real research figures with captions when their meaning is known. Highlight cards may pair one image with one title, but the full description belongs on the detail or highlights page.

### News and publications

News records begin with `YYYY.MM`, then one factual sentence. Use “published in” for journals, not “published on.” Congratulations may appear for personal awards, but the archive should not sound like a social feed.

Publication records preserve title, author order, contribution markers, journal, volume or article number, pages where available, year, and DOI or publisher link. Paper titles remain verbatim. Display publication years newest first and keep citation punctuation consistent within a page.

### People

Each member record uses the same field order: name, role or degree, affiliation or present position, research interest, then contact links. Never infer missing research interests, titles, destinations, or alumni status. Chinese names remain alongside Romanized names when supplied by the source.

### Teaching and contact

Course pages use stable labeled fields: teacher, teaching group, venue, schedule, target students, room, semester, credits, and course type. Contact details use one approved canonical rendering across Contact, People, and the footer.

### Bilingual content

English and Chinese pages share a `translationKey` and equivalent section coverage. Equivalent means the same facts, claims, caveats, links, people, and dates—not identical sentence structure. A placeholder in one language must never masquerade as the translation of a complete page; mark incomplete translations explicitly during migration and keep them out of production navigation if necessary.

### Interaction and accessibility

All interactive elements have a visible focus indication implemented as `outline: {focus.width} solid {focus.color}` with `{focus.offset}` outline offset; the focus treatment must never fill or obscure the control. Provide usable hover and active states and descriptive accessible names. Respect `prefers-reduced-motion`; no essential information depends on animation. Images require meaningful alt text when their content is known and empty alt text only when truly decorative.

## Do's and Don'ts

### Do

- Use PKU red sparingly and consistently as the institutional thread.
- Let scientific titles, names, figures, dates, and references provide the visual interest.
- Keep long-form pages readable and retrieval-friendly with stable headings and links.
- Preserve legacy URLs through Hugo aliases and record intentional URL changes.
- Normalize obvious source grammar and markup defects while retaining a traceable source archive.
- Test every major template at desktop and mobile widths with keyboard navigation.

### Don't

- Do not make the site resemble a startup landing page, SaaS dashboard, or personal portfolio template.
- Do not use gradients, glassmorphism, neon cyan or purple, dark-mode theatrics, parallax, autoplay, or animated counters.
- Do not create a “card soup” where news, publications, people, and research all use the same rounded rectangle.
- Do not use stock laboratory imagery, decorative molecules, AI-generated science illustrations, or invented diagrams.
- Do not use oversized display type on interior pages or let the hero hide the group’s research statement below the fold.
- Do not publish truncated CMS excerpts, broken emphasis markup, duplicate records, or unverified scientific rewrites.
- Do not add decorative emoji beyond the approved language-switch globe.
