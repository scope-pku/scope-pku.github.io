# Xu Group Website Page-by-Page Optimization

This checklist tracks the English redesign first. Shared templates must remain
compatible with the existing Chinese placeholders; Chinese content parity begins
only after the English design is approved.

## Status rule

- Keep an item unchecked while it is being designed, implemented, reviewed, or
  corrected.
- Mark an item complete only after its route passes the page-level definition of
  done below.
- Preserve the optional, Git-ignored `source/xulm.pku.edu.cn/` as the immutable comparison source when it is available locally.
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
- Verify the lowercase page route.
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
  and lowercase routes.

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

- [x] **Photos index** `/photos/` — create an editorial entry point that
  preserves the role of each gallery.
- [x] **Group Members** `/photos/group-members/` — compare
  `Photos/Group_Members.htm`; preserve three natural-ratio images.
- [x] **Meetings** `/photos/meetings/` — compare `Photos/Meetings.htm`; preserve
  two natural-ratio images.
- [x] **Have Fun** `/photos/have-fun/` — compare `Photos/Have_Fun.htm`; preserve
  three natural-ratio images.
- [x] **Dine Together** `/photos/dine-together/` — compare the legacy typo route
  `Photos/Dine_Toghter.htm`; preserve its image but publish only the lowercase
  route.
- [x] **Graduation** `/photos/graduation/` — compare `Photos/Graduation.htm`;
  preserve four natural-ratio images.

## 7. Contact and English release gate

- [x] **Contact** `/contact/` — compare `Contact_Us.htm`; use the canonical
  address, office, telephone, email, personal page, and student-office details.
- [x] Run the final English route, content-count, asset, accessibility,
  responsive, and broken-link regression checks.
- [x] Resolve final visual review notes: use one left Home text column with a
  right-side figure, alternate Research text and figures with left-aligned
  references, format the footer as a postal block, and move the SVG language
  switch to the right side of the navigation row.
- [x] Review the complete English visual system and normalize mobile gutters,
  interior title scale, archive reading width, and section-aware language links.
- [x] Replace the mobile horizontal navigation strip with an accessible native
  disclosure drawer containing the current page and language switch.
- [x] Rebuild the bilingual footer as three responsive blocks for the PKU
  wordmark, canonical contact details, and locale-specific quick links.
- [ ] Obtain final English visual approval and tag the English design as locked.

## 8. Chinese localization after English approval

### 中文化规则与逐页验收

- [x] 确认中文化原则：中文版与已核准英文版使用相同的信息层级、组件、
  图片角色与响应式排版。
- [x] 中文不要求逐句直译；优先使用自然、专业、符合中文学术网站习惯的
  表达。英文原文已经准确自然时，不为制造差异而改写。
- [x] 论文题目、期刊名称与作者名单保留英文原文，不翻译、不改写作者顺序；
  年份、卷期、页码、DOI 与原始链接保持不变。
- [ ] 每次只处理一个页面；当前页面完成内容核对、桌面与手机检查并获得确认后，
  才开始下一页。
- [ ] 每个中文页面必须与英文对应页面共享正确的 `translationKey`，并验证
  `CN` / `EN` 切换会到达对应页面，而不是退回首页。
- [ ] 每页核对事实、数字、姓名、机构、图片、链接、科学条件与谨慎措辞；
  不补写未经来源支持的结论、履历、研究方向或宣传性表述。
- [ ] 每页在 1440 px 桌面、768 px 平板与 390 px 手机检查相同版式结构、
  阅读顺序、图片裁切、标题层级、键盘焦点、对比度及水平溢出。
- [ ] 每页完成后运行干净 Hugo 构建、勾选对应项目，并建立一个聚焦提交。

### 8.1 Shared Chinese interface

- [x] **共用界面** — 核对中文页首、导航、面包屑、语言切换、移动抽屉、
  Footer、联系方式与机构名称；只本地化文字，不改变已核准的英文版尺寸和布局。

### 8.2 Home and Research

- [x] **首页** `/zh/` — 对照 `/`，中文化课题组简介、研究方向、研究亮点与
  近期新闻；保持宽幅合照、左文右图和相同首屏节奏。
- [x] **研究方向** `/zh/research/` — 对照 `/research/`，按相同图文交替结构
  中文化研究问题、方法、证据、限制与开放方向；参考文献条目保持英文原文。

### 8.3 People

- [x] **成员列表** `/zh/people/` — 对照 `/people/`，保留全部成员、照片、
  英文姓名、中文姓名、学历、研究方向、邮箱与分类顺序，不推断空缺字段。
- [x] **徐莉梅个人页** `/zh/people/limei-xu/` — 对照 `/people/limei-xu/`，
  中文化职称、单位、联系方式与资源标签，保持资料来源和链接不变。

### 8.4 News

- [x] **最新消息** `/zh/news/` — 对照 `/news/`，逐条中文化新闻叙述并保留
  `YYYY.MM` 日期、论文英文题目、期刊名称与原始链接。
- [x] **全部新闻与活动** `/zh/news/all-news/` — 对照 `/news/all-news/`，
  保留全部记录、年份与分类结构；论文相关元数据继续使用英文原文。

### 8.5 Publications

- [x] **成果首页** `/zh/publications/` — 对照 `/publications/`，中文化栏目说明
  与导航标签，保持相同入口与记录统计。
- [x] **研究亮点** `/zh/publications/highlights/` — 对照
  `/publications/highlights/`，中文化说明文字；论文题目、作者、期刊与链接
  保持英文原文。
- [x] **论文列表** `/zh/publications/full-list/` — 对照
  `/publications/full-list/`，完整保留全部英文引文、作者顺序、年份分组、DOI
  与期刊信息，不翻译论文题目。
- [x] **学位论文** `/zh/publications/theses/` — 对照
  `/publications/theses/`，保留姓名、题目、年份、学位类别和既有中英文信息，
  不自行补译缺失内容。

### 8.6 Teaching

- [x] **教学首页** `/zh/teaching/` — 对照 `/teaching/`，中文化课程说明与年份
  导航，保持课程字段和页面结构一致。
- [x] **2022 年课程** `/zh/teaching/2022/` — 对照 `/teaching/2022/`。
- [x] **2021 年课程** `/zh/teaching/2021/` — 对照 `/teaching/2021/`。
- [x] **2020 年课程** `/zh/teaching/2020/` — 对照 `/teaching/2020/`。
- [x] **2019 年课程** `/zh/teaching/2019/` — 对照 `/teaching/2019/`。

### 8.7 Photos

- [x] **照片首页** `/zh/photos/` — 对照 `/photos/`，中文化图库标题、简介与
  图片说明，保持图片数量、顺序和自然比例。
- [x] **课题组成员** `/zh/photos/group-members/` — 对照
  `/photos/group-members/`。
- [x] **会议活动** `/zh/photos/meetings/` — 对照 `/photos/meetings/`。
- [x] **休闲活动** `/zh/photos/have-fun/` — 对照 `/photos/have-fun/`。
- [x] **聚餐** `/zh/photos/dine-together/` — 对照 `/photos/dine-together/`，
  仅发布小写地址。
- [x] **毕业留影** `/zh/photos/graduation/` — 对照 `/photos/graduation/`。

### 8.8 Contact

- [x] **联系我们** `/zh/contact/` — 对照 `/contact/`，中文化负责人、办公地点、
  学生办公室与 Join Us 文案；电话、邮箱、地址事实和个人主页链接保持不变。

### 8.9 Chinese release gate

- [x] 检查所有中英文小写路由、`translationKey`、alternate-language metadata、
  语言切换与 404 行为。
- [x] 检查中英文记录数量、图片资产、外部链接、邮件和电话链接一致且无遗漏。
- [x] 完成 1440 / 768 / 390 px 全站响应式与无障碍回归，确认无水平溢出。
- [x] 运行最终干净 Hugo 构建并检查无 VSB 资源、无构建警告和无未提交改动。
- [ ] 获得中文版最终视觉与文字确认，标记双语网站可发布。

## 9. Shared implementation cleanup

- [x] 在不改变网站结构与显示的前提下，将介面文字改用 Hugo i18n，外置手机
  菜单脚本，抽取共用联络资料，并将照片、论文与学位论文改为项目级共享来源。

## 10. Production replacement preparation

- [x] 在隔离目录验证 Boda 可直接提供静态 HTML、内联 CSS、图片与 JavaScript。
- [x] 下载 2026-07-16 13:49 的旧站网站包及 `.sto` 附属文件，记录 SHA-256，
  并确认 Boda 显示 `全检通过`。
- [x] 确认 Boda 网站包用于 CMS 回滚，不能把普通 Hugo ZIP 当作网站包导入。
- [x] 确认批量上传支持一次选择多个文件，但不保留目录树；当前正式输出分布在
  46 个全小写目录中。
- [x] 确认裸域名当前使用 `/index.htm`，并在正式建置脚本中以真实首页覆盖
  Hugo 的根目录跳转别名。
- [x] 增加 `tools/build_boda_release.sh`，生成带校验清单的正式静态产物。
- [ ] 将 `backups/boda/2026-07-16/` 复制到本机以外的第二个存储位置。
- [ ] 获得英文版最终视觉批准及中文版最终视觉、文字批准。
- [ ] 整理当前工作区，建立干净的发布提交与 release tag。
- [ ] 向 Boda 管理员确认是否提供保留目录树的静态文件上传、服务器同步或正式
  发布接口；若没有，再批准 46 个目录的 UI 批量上传方案。
- [ ] 指定维护时段、上线操作者、验收人及回滚决定人。
- [ ] 按 `BODA_DEPLOYMENT.md` 完成发布前演练和逐项验收，但不得在正式站试做
  网站包导入。
