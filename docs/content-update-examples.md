# 内容更新示例

本页提供可复制的最小示例，用于维护现有网站内容。开始前先阅读 [`AGENTS.md`](../AGENTS.md) 和 [`DESIGN.md`](../DESIGN.md)。示例中的 `REPLACE_...`、示例姓名、示例标题、日期、链接和文件名都必须替换为已核准的真实内容；不要把示例文字直接发布。

## 共同规则

1. 本地如有 `source/xulm.pku.edu.cn/`，它只是被 Git 忽略的旧站只读快照，不得编辑。
2. 中文与英文必须在事实、人物、日期、链接、科学主张和限定语上等价；可以自然翻译，不要求逐句直译。
3. 图片和 PDF 放在 `site/static/media/`，页面中使用 `/media/文件名` 引用。为通过 Boda release 构建，文件主名只使用 ASCII 英文字母、数字、`-` 和 `_`，不要使用空格或中文。
4. 不要手工编辑 `site/public/` 或 `dist/boda-site/`；它们都是构建输出。
5. 现有列表大多不自动排序，文件或 JSON 数组中的先后顺序就是页面顺序。新增最新内容时通常插在同类内容最前面。
6. JSON 中对象之间必须有逗号，最后一个对象后不能多写逗号。
7. 不要运行 `tools/migrate_english.py`。

## 快速索引

| 要更新的内容 | 主要源文件 | 还需同步 |
| --- | --- | --- |
| 新闻 | `site/data/recent_news.json` | `site/content/en/news/_index.md`、`site/content/zh/news/_index.md` |
| 论文亮点 | `site/data/highlights.json` | 中英文 `publications/highlights.md`、亮点图片；PDF 仅在提供下载时需要 |
| 研究主题 | 中英文 `research/_index.md` | 研究图片 |
| 完整论文列表 | `site/assets/data/full-publication-list.md` | 无单独中文版；中英文路由共用此列表 |
| 课题组成员 | `site/data/people.json` | 成员肖像；只有添加个人详情链接时才需新建中英文详情页 |
| 照片 | `site/data/photos.json` | 照片文件；新增相册或修改相册标题时还需中英文 `photos/*.md` |
| 教学 | 中英文 `teaching/_index.md` 与年度 `teaching/YYYY.md` | 修改教学主图时还需对应图片 |

## 修改已有内容：先找唯一数据源

修改既有记录时，不要复制一份新数据。先按下表修改现有记录，再检查所有同步来源：

| 内容 | 修改位置 |
| --- | --- |
| 新闻 | 首页短文改 `site/data/recent_news.json`；新闻页正文同时改中英文 `news/_index.md`；已进入归档的记录还要同步中英文 `all-news.md` |
| 论文亮点 | 改 `site/data/highlights.json` 的首页摘要与尺寸，并同步中英文 `publications/highlights.md` 的正文和链接 |
| 研究主题 | 同时修改中英文 `research/_index.md` 中对应的 `research-story` |
| 完整论文列表 | 只修改共享的 `site/assets/data/full-publication-list.md` |
| 成员 | 修改 `site/data/people.json` 中原有成员对象；个人详情页存在时再同步对应中英文页面 |
| 照片 | 图片、替代文本和图注改 `site/data/photos.json`；相册标题与摘要改中英文 `photos/*.md` |
| 教学 | 教学首页改中英文 `teaching/_index.md`；年度课程改同年份的中英文 `teaching/YYYY.md` |

修改时遵守以下原则：

1. 保留已有 `translationKey`、`gallery` key、文件路径和 URL；只有明确决定迁移时才改这些标识。
2. 中英文成对记录要在同一次修改中更新，不能只修正一种语言。
3. 更换图片时同步修改所有引用路径和真实 `width`、`height`，并重新核对两种语言的 `alt` 与 caption。
4. 删除记录前先确认它是否同时被首页、栏目页、详情页或共享数据读取；不要只删除其中一个副本。
5. 修改数组或 Markdown 列表时保留预期顺序，不依赖 Hugo 自动按日期排序。

---

## 示例一：新增一条新闻

一条需要同时出现在首页和新闻页的新闻，要修改三个文件。以下示例使用 `2026.07`，实际更新时替换日期、文字和链接。

### 1. 更新首页新闻数据

在 `site/data/recent_news.json` 数组开头加入一个对象。首页按数组顺序显示所有条目，因此最新新闻放在最前面：

```json
{
  "date": "2026.07",
  "text": "REPLACE_WITH_APPROVED_ENGLISH_NEWS_TEXT.",
  "text_zh": "替换为已核准的中文新闻内容。",
  "url": "https://example.org/replace-with-approved-link"
}
```

如果新闻没有目标链接，使用空字符串：

```text
"url": ""
```

`text` 与 `text_zh` 是首页显示的短文本，必须表达同一事实。日期沿用当前的 `YYYY.MM` 格式，并使用两位月份。

### 2. 更新英文新闻页

在 `site/content/en/news/_index.md` front matter 结束后的新闻列表最前面加入：

```markdown
{{< news-row date="2026.07" >}}REPLACE_WITH_APPROVED_ENGLISH_NEWS_TEXT.{{< /news-row >}}
```

带链接的例子：

```markdown
{{< news-row date="2026.07" >}}Our paper "[REPLACE_WITH_PAPER_TITLE](https://example.org/replace-with-paper-url)" was published in *REPLACE_WITH_JOURNAL*.{{< /news-row >}}
```

### 3. 更新中文新闻页

在 `site/content/zh/news/_index.md` 对应位置加入语义等价的条目：

```markdown
{{< news-row date="2026.07" >}}论文“[替换为论文标题](https://example.org/replace-with-paper-url)”发表于 *替换为期刊名称*。{{< /news-row >}}
```

两种语言使用相同日期和目标链接。若这条新闻也应进入完整历史归档，再按现有年份结构同时更新：

- `site/content/en/news/all-news.md`
- `site/content/zh/news/all-news.md`

不要只更新首页 JSON；否则首页与 `/news/` 会不一致。

---

## 示例二：新增一个论文亮点

论文亮点页的正文、首页摘要和图片尺寸来自不同文件。最小完整更新需要：

- `site/data/highlights.json`
- `site/content/en/publications/highlights.md`
- `site/content/zh/publications/highlights.md`
- `site/static/media/highlight-REPLACE.png` 或 `.jpg`
- 可选的 `site/static/media/highlight-REPLACE.pdf`

### 1. 准备图片和可选 PDF

把已核准的图片放入：

```text
site/static/media/highlight-REPLACE.png
```

记录图片的真实像素宽度和高度，不要猜测。若提供论文下载，再放入：

```text
site/static/media/highlight-REPLACE.pdf
```

为通过当前 Boda release 构建检查，文件主名只使用 ASCII 英文字母、数字、`-` 和 `_`；建议延续 `highlight-数字` 的命名方式，并使用平台支持的图片或 PDF 扩展名。

### 2. 添加亮点数据

在 `site/data/highlights.json` 中加入：

```json
{
  "title": "REPLACE_WITH_OFFICIAL_PAPER_TITLE",
  "image": "/media/highlight-REPLACE.png",
  "width": 1600,
  "height": 1000,
  "url": "https://example.org/replace-with-paper-url",
  "summary": "REPLACE_WITH_APPROVED_ENGLISH_SUMMARY.",
  "summary_zh": "替换为与英文等价的已核准中文摘要。"
}
```

把 `width` 和 `height` 替换为图片真实尺寸。`title` 通常保留论文正式标题；首页中文版本会使用同一个标题，并用 `summary_zh` 显示中文摘要。

此 JSON 记录不是只供首页使用：`research-highlight` 短代码也会按 `image` 查找图片尺寸。因此，即使亮点不排在首页前三条，也必须添加匹配的 JSON 记录。

首页只显示 `highlights.json` 的前三项。如果新亮点应出现在首页，把它放到数组前面；如果不应改变首页前三项，就放在相应历史位置。

### 3. 添加英文亮点正文

在 `site/content/en/publications/highlights.md` 的目标位置加入：

```markdown
{{< research-highlight title="REPLACE_WITH_OFFICIAL_PAPER_TITLE" image="/media/highlight-REPLACE.png" >}}
REPLACE_WITH_APPROVED_ENGLISH_DESCRIPTION.

[REPLACE_WITH_JOURNAL_CITATION](https://example.org/replace-with-paper-url) · [PDF](/media/highlight-REPLACE.pdf)
{{< /research-highlight >}}
```

没有 PDF 时删除 `· [PDF](...)`，不要保留失效链接。

### 4. 添加中文亮点正文

在 `site/content/zh/publications/highlights.md` 的对应位置加入：

```markdown
{{< research-highlight title="REPLACE_WITH_OFFICIAL_PAPER_TITLE" image="/media/highlight-REPLACE.png" >}}
替换为与英文等价的已核准中文介绍。

[替换为期刊引用](https://example.org/replace-with-paper-url) · [PDF](/media/highlight-REPLACE.pdf)
{{< /research-highlight >}}
```

中英文短代码的 `image` 必须与 `highlights.json` 完全一致，否则构建时无法取得图片尺寸。

---

## 示例三：新增一个研究主题

研究主题只在中英文研究页维护，不需要新增 JSON。准备一张已核准图片，例如：

```text
site/static/media/research-new-topic.jpg
```

### 1. 添加英文主题

在 `site/content/en/research/_index.md` 的目标顺序位置加入：

```markdown
{{< research-story title="REPLACE_WITH_APPROVED_ENGLISH_TITLE" image="/media/research-new-topic.jpg" width="1600" height="1000" alt="REPLACE_WITH_ACCURATE_ENGLISH_ALT_TEXT" caption="REPLACE_WITH_APPROVED_ENGLISH_CAPTION" >}}

REPLACE_WITH_APPROVED_ENGLISH_DESCRIPTION.

{{< /research-story >}}
```

### 2. 添加中文主题

在 `site/content/zh/research/_index.md` 的对应位置加入：

```markdown
{{< research-story title="替换为已核准的中文标题" image="/media/research-new-topic.jpg" width="1600" height="1000" alt="替换为准确描述图片内容的中文替代文本" caption="替换为已核准的中文图注" >}}

替换为与英文在事实、科学主张和限定语上等价的已核准中文介绍。

{{< /research-story >}}
```

`width` 和 `height` 必须是图片的真实像素尺寸。两种语言通常使用同一图片，但 `title`、`alt`、`caption` 和正文分别使用自然的对应语言。

如果一个主题确实需要第二张图，可在开始短代码中增加：

```text
image2="/media/research-new-topic-detail.jpg" width2="1600" height2="1000" alt2="..." caption2="..."
```

只有现有模板支持的参数才能使用；当前第二张图参数包括 `image2`、`width2`、`height2`、`alt2`、`caption2`。主题显示顺序就是 Markdown 中的先后顺序。

---

## 示例四：新增一条论文列表记录

完整论文列表的唯一正文来源是：

```text
site/assets/data/full-publication-list.md
```

`site/content/en/publications/full-list.md` 和 `site/content/zh/publications/full-list.md` 只是中英文页面外壳，不要把论文条目写入这两个文件。

在正确年份标题下加入一个 Markdown 列表项：

```markdown
## 2026

- REPLACE_WITH_AUTHORS. "REPLACE_WITH_ARTICLE_TITLE". REPLACE_WITH_JOURNAL VOLUME, PAGES OR ARTICLE NUMBER. (2026).
```

如果年份标题已经存在，只添加 `- ...` 条目，不要重复创建 `## 2026`。如果是新年份，在文件顶部按降序增加新年份标题。

示例格式应按相邻条目的现有书目风格调整。作者顺序、共同第一作者/通讯作者标记、题目、期刊、卷页、年份和 DOI 必须来自核准的正式记录。此共享列表会同时显示在：

- `/publications/full-list/`
- `/zh/publications/full-list/`

因此不需要维护一份翻译后的中文书目列表。

---

## 示例五：新增一位课题组成员

成员目录的唯一数据来源是：

```text
site/data/people.json
```

先把肖像放到：

```text
site/static/media/people-REPLACE.jpg
```

再把成员对象加入正确的 `people` 数组。现有分类名称会影响模板布局和标签，不要改名：

- `Group Leader`
- `Visiting Scholar`
- `Post-doctor`
- `Graduate Students`
- `Undergraduate`
- `Alumni — Postdocs and Ph.D.s`

以下是加入 `Graduate Students` 的可复制示例：

```json
{
  "name": "Example Researcher",
  "name_en": "Example Researcher",
  "name_zh": "示例成员",
  "details": [
    "REPLACE_WITH_APPROVED_ENGLISH_EDUCATION_OR_POSITION"
  ],
  "details_zh": [
    "替换为与英文等价的已核准教育或职位信息"
  ],
  "email": "replace-with-approved-address@pku.edu.cn",
  "research_interest": "REPLACE_WITH_APPROVED_ENGLISH_RESEARCH_INTERESTS",
  "research_interest_zh": "替换为与英文等价的已核准研究兴趣",
  "image": "/media/people-REPLACE.jpg",
  "status": "current"
}
```

字段说明：

- `name`：默认主名，也是英文页面的主标题和其他显示逻辑的回退值。研究生分类会另行显示 `name_zh`，因此新研究生的 `name` 建议只写英文名，避免中文名重复。
- `name_en`：中文页面存在此字段时，用作卡片主标题。
- `name_zh`：中文页面会用于中文肖像替代文本并显示为中文副标题；研究生分类的英文页面也会显示此副标题。
- `details`、`details_zh`：数组，可写多行经历；两种语言保持等价。
- `role`、`role_zh`：需要单独显示职位时可添加。
- `research_interest`、`research_interest_zh`：没有已核准内容时可以省略或使用空字符串，不要推断。
- `email`、`telephone`、`personal_page`、`cv`：有已核准信息时才添加。
- `image`：模板会直接渲染，必须指向已存在的肖像。
- `status`：当前成员使用 `current`，校友使用 `alumni`。当前模板不依赖它筛选，但仍应保持数据准确。
- `profile`：只有已经创建并验证对应个人详情页时才添加；否则省略，避免生成 404 链接。

成员和分类都按 JSON 中的顺序显示。把新成员放在经过确认的位置，不要依赖姓名或年份自动排序。

---

## 示例六：新增或修改照片

照片文件放在 `site/static/media/`，相册数据集中维护在：

```text
site/data/photos.json
```

### 1. 向现有相册增加一张照片

以下示例向 `meetings` 相册增加一张照片。先加入文件：

```text
site/static/media/photos-meetings-03.jpg
```

再在 `site/data/photos.json` 的 `"meetings"` → `"images"` 数组中加入：

```json
{
  "src": "/media/photos-meetings-03.jpg",
  "width": 1600,
  "height": 1067,
  "alt": "REPLACE_WITH_ACCURATE_ENGLISH_DESCRIPTION_OF_THE_PHOTO",
  "alt_zh": "替换为准确描述照片内容的中文替代文本",
  "caption": "REPLACE_WITH_APPROVED_ENGLISH_CAPTION, INCLUDING_DATE_OR_LOCATION_ONLY_IF_CONFIRMED.",
  "caption_zh": "替换为与英文等价的已核准中文图注；日期和地点必须经过确认。"
}
```

把 `width` 和 `height` 换成照片真实像素尺寸。`alt` 与 `alt_zh` 要描述画面内容；`caption` 与 `caption_zh` 可补充已确认的事件、地点和日期。没有图注时可同时省略两个 caption 字段，但不要省略有内容意义的 alt。

相册按 `images` 数组顺序显示。第一张照片还会作为 `/photos/` 相册索引的预览图，并在相册页占据首个大图位置；普通新增照片通常放在数组末尾。若要更换封面，把经过确认的照片对象移到第一项。

只向现有相册添加照片时，不需要修改中英文 Markdown 相册页。

### 2. 修改现有照片或相册文字

- 修改图片、alt 或图注：直接编辑 `site/data/photos.json` 中原有图片对象；换图时同时更新 `src`、`width` 和 `height`。
- 修改相册标题或摘要：同时编辑相同路径的中英文页面，例如 `site/content/en/photos/meetings.md` 与 `site/content/zh/photos/meetings.md`。
- 保留两页相同的 `translationKey`、`weight`、`layout: gallery` 和 `gallery`；`gallery` 必须与 `photos.json` 的 key 完全一致。

### 3. 新增一个相册

先在 `site/data/photos.json` 顶层增加一个至少包含一张图片的相册。例如：

```text
"field-trips": {
  "images": [
    {
      "src": "/media/photos-field-trips-01.jpg",
      "width": 1600,
      "height": 1067,
      "alt": "REPLACE_WITH_ACCURATE_ENGLISH_ALT_TEXT",
      "alt_zh": "替换为准确的中文替代文本",
      "caption": "REPLACE_WITH_APPROVED_ENGLISH_CAPTION.",
      "caption_zh": "替换为与英文等价的已核准中文图注。"
    }
  ]
}
```

这个片段是顶层 JSON 属性，插入现有对象时要注意与相邻相册之间的逗号。

然后创建英文页面 `site/content/en/photos/field-trips.md`：

```markdown
---
title: "Field Trips"
translationKey: photos-field-trips
summary: "REPLACE_WITH_APPROVED_ENGLISH_GALLERY_SUMMARY."
weight: 60
layout: gallery
gallery: field-trips
---
```

同时创建中文页面 `site/content/zh/photos/field-trips.md`：

```markdown
---
title: 外出活动
translationKey: photos-field-trips
summary: "替换为与英文等价的已核准中文相册摘要。"
weight: 60
layout: gallery
gallery: field-trips
---
```

两页使用相同文件名、`translationKey`、`weight` 和 `gallery`。`weight` 越小，栏目中的排序越靠前；选择未占用的值，并按预期栏目顺序设置。

---

## 示例七：新增或修改教学内容

教学内容由中英文 Markdown 成对维护，不使用独立 data 文件。

### 1. 修改教学首页

同时修改：

- `site/content/en/teaching/_index.md`
- `site/content/zh/teaching/_index.md`

正文用于课程介绍和参考书目。首页主图由以下 front matter 字段控制：

```yaml
featureImage: "/media/teaching-thermodynamics.png"
featureImageWidth: 1350
featureImageHeight: 899
featureImageAlt: "REPLACE_WITH_ACCURATE_ALT_TEXT_IN_THE_PAGE_LANGUAGE"
```

更换主图时，把文件放入 `site/static/media/`，在两种语言页面中填写真实尺寸，并分别提供准确的 `featureImageAlt`。两页继续使用相同的 `translationKey: teaching`。

### 2. 修改现有年度课程

找到同一年度的中英文文件，例如：

- `site/content/en/teaching/2022.md`
- `site/content/zh/teaching/2022.md`

直接修改 `courses` 数组中的对应课程。课程按数组顺序显示；`title` 和 `teacher` 会直接输出，应始终提供。以下字段按现有模板支持，可在有核准信息时使用：

- `teaching_group`：字符串数组
- `venue`
- `schedule`
- `target_students`
- `classroom`
- `semester`
- `credits`
- `course_type`

中英文课程数量、顺序、教师、时间、学分和课程性质必须对应。

### 3. 新增一个教学年度

创建相同文件名的中英文年度页面。英文 `site/content/en/teaching/2026.md` 示例：

```yaml
---
title: "Teaching in 2026"
translationKey: teaching-2026
summary: "Course records for 2026."
weight: 5
courses:
  - title: "REPLACE_WITH_APPROVED_ENGLISH_COURSE_TITLE"
    teacher: "REPLACE_WITH_APPROVED_ENGLISH_TEACHER_NAME"
    teaching_group:
      - "REPLACE_WITH_APPROVED_ENGLISH_NAME"
    venue: "REPLACE_WITH_APPROVED_ENGLISH_VENUE"
    schedule: "REPLACE_WITH_APPROVED_ENGLISH_SCHEDULE"
    target_students: "REPLACE_WITH_APPROVED_ENGLISH_STUDENT_GROUP"
    classroom: "REPLACE_WITH_APPROVED_ENGLISH_CLASSROOM"
    semester: "REPLACE_WITH_APPROVED_ENGLISH_SEMESTER"
    credits: "REPLACE_WITH_APPROVED_CREDITS"
    course_type: "REPLACE_WITH_APPROVED_ENGLISH_COURSE_TYPE"
---
```

中文 `site/content/zh/teaching/2026.md` 示例：

```yaml
---
title: "2026 年课程"
translationKey: teaching-2026
summary: "2026 年课程记录。"
weight: 5
courses:
  - title: "替换为已核准的中文课程名称"
    teacher: "替换为已核准的中文教师姓名"
    teaching_group:
      - "替换为对应的教学组成员姓名"
    venue: "替换为已核准的中文教学地点"
    schedule: "替换为已核准的中文上课时间"
    target_students: "替换为已核准的中文授课对象"
    classroom: "替换为已核准的中文教室"
    semester: "替换为已核准的中文学期"
    credits: "替换为已核准的学分"
    course_type: "替换为已核准的中文课程性质"
---
```

注意：

- 两页的 `translationKey` 和 `weight` 必须相同。
- `title` 必须包含四位年份；年度导航会从标题中提取 `[0-9]{4}`。
- `weight` 越小，年度导航越靠前。新增年度前先检查现有年度页面；若新年度要排在最前，使用小于当前最小值的未占用值。当前最小值是 `10`，所以示例使用 `5`。
- 没有核准值的可选字段应从两种语言中同时删除，不要发布 `REPLACE_...` 占位文字。

---

## 每次更新后的验证

从仓库根目录执行 JSON 语法检查（只需检查本次修改过的 JSON）：

```sh
python3 -m json.tool site/data/recent_news.json >/dev/null
python3 -m json.tool site/data/highlights.json >/dev/null
python3 -m json.tool site/data/people.json >/dev/null
python3 -m json.tool site/data/photos.json >/dev/null
```

运行 Hugo 构建：

```sh
hugo --source site --cleanDestinationDir
```

准备发布候选时还必须运行生产 Boda 构建；它会额外检查文件名、正式 URL、开发引用和 Boda 输出约束：

```sh
tools/build_boda_release.sh
```

需要浏览器检查时运行：

```sh
hugo server --source site
```

根据改动检查对应的中英文路径：

| 内容 | 英文 | 中文 |
| --- | --- | --- |
| 首页新闻与首页亮点 | `/` | `/zh/` |
| 新闻 | `/news/` | `/zh/news/` |
| 论文亮点 | `/publications/highlights/` | `/zh/publications/highlights/` |
| 研究主题 | `/research/` | `/zh/research/` |
| 完整论文列表 | `/publications/full-list/` | `/zh/publications/full-list/` |
| 成员 | `/people/` | `/zh/people/` |
| 照片 | `/photos/` | `/zh/photos/` |
| 教学 | `/teaching/` | `/zh/teaching/` |
| 新相册示例 | `/photos/field-trips/` | `/zh/photos/field-trips/` |
| 新教学年度示例 | `/teaching/2026/` | `/zh/teaching/2026/` |

最后检查：

- 新图片和 PDF 能打开，没有 404。
- 中英文内容表达同一事实，日期和链接一致。
- 图片 `alt` 和图注准确，不从文件名推断科学含义。
- 最新内容处于预期顺序；论文亮点如需显示在首页，位于 `highlights.json` 前三项。
- 没有修改本地 `source/`、`site/public/`、`dist/` 或 `site/data/migration-assets.json`。
- `git diff --check` 无空白错误。

构建成功只证明 Hugo 可以生成页面；发布到 Boda 前仍须按 [`operator-guide.md`](operator-guide.md) 和 [`BODA_DEPLOYMENT.md`](../BODA_DEPLOYMENT.md) 完成发布前检查。