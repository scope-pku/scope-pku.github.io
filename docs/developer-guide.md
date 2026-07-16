# 开发者指南

本指南面向维护 `site/` Hugo 项目的开发者。它说明内容、模板、样式、资源和发布构建之间的关系；具体的线上操作和 Boda 安全流程请以 `BODA_DEPLOYMENT.md` 为准。

## 开始前：必须阅读的文件

在修改任何布局、样式、组件或公开内容前，先从仓库根目录阅读：

- `AGENTS.md`：项目范围、双语内容原则、`source/xulm.pku.edu.cn/` 的只读约束、URL 和 Boda 规则。
- `DESIGN.md`：视觉、排版、间距、组件、双语编辑和可访问性规范。
- `site/README.md`：Hugo 预览、双语页面配对和历史迁移说明。
- `BODA_DEPLOYMENT.md`：发布候选构建、验证、上传和回滚流程。
- `docs/content-update-examples.md`：新增或修改新闻、论文亮点、研究主题、论文列表、成员、照片和教学内容时使用的可复制最小示例。

`source/xulm.pku.edu.cn/` 是从旧站抓取的 HTML 快照，只能用于核对路径、事实、链接和素材；它是只读参考，不得编辑，也不能把快照中的未核实内容直接扩写到新站。

开发时保持中文和英文在事实、主张、限定语、链接、人物和日期上的等价。等价不要求逐句直译，但不得让某种语言包含另一种语言没有的未经批准的信息。

## 项目结构

```text
.
├── AGENTS.md                 # 工作规则
├── DESIGN.md                 # 设计与编辑规范
├── BODA_DEPLOYMENT.md        # Boda 发布与回滚说明
├── source/xulm.pku.edu.cn/   # 旧站只读 HTML 快照
├── site/
│   ├── hugo.yaml             # Hugo、语言和菜单配置
│   ├── content/en/           # 英文内容（默认语言，根路径）
│   ├── content/zh/           # 中文内容（/zh/ 路径）
│   ├── layouts/              # base 模板、默认模板、栏目模板和短代码
│   ├── assets/               # Hugo Pipes 可处理的 CSS、JavaScript 等源资源
│   ├── static/                # 原样复制到输出目录的静态资源
│   ├── data/                  # 模板通过 hugo.Data 读取的 YAML、JSON 等结构化数据
│   ├── i18n/                  # 界面文案翻译（`en.yaml`、`zh.yaml`）
│   ├── archetypes/            # 新内容的可选模板
│   └── public/                # 普通 Hugo 构建输出，不是源文件
├── tools/build_boda_release.sh # 生产 Boda 构建入口
├── tools/bodacli              # Boda CLI 正式入口
└── dist/boda-site/            # Boda 发布候选输出（构建时生成）
```

命令默认从仓库根目录执行。Hugo 源目录是 `site/`；不要把 `site/public/` 当作手工维护的内容。

## Hugo 语言与路由模型

`site/hugo.yaml` 当前设置：

- `defaultContentLanguage: en`：英文是默认语言。
- `defaultContentLanguageInSubdir: false`：英文页面位于站点根路径，例如 `/news/`；中文页面位于 `/zh/`，例如 `/zh/news/`。
- `languages.en.contentDir: content/en`、`languages.zh.contentDir: content/zh`：两种语言从对应目录读取内容。
- `disableAliases: true`：Hugo 不生成 aliases 页面。任何旧 URL 兼容工作都必须先做出明确决策，不能假定添加 `aliases` 就会自动生效。
- `disableKinds` 禁用了 RSS、taxonomy 和 term 页面；不要为这些不存在的 kind 编写依赖。

同一双语页面应在两种语言目录中使用相同的相对路径，并设置相同的 `translationKey`。Hugo 据此关联语言版本并生成语言切换链接。栏目首页使用 `_index.md`，普通页面使用 `*.md`；子目录可以继续包含 `_index.md` 和子页面。

路径目录和 slug 使用 lowercase，并尽量保留已经公开的 URL。新增或改变 URL 前，记录变更并先决定兼容策略；当前 `disableAliases=true` 时尤其不能把别名当作已经实现的兼容方案。

## Front matter 与 `translationKey`

Front matter 位于 Markdown 文件开头的 `---` 块中。常见字段包括：

- `title`：页面标题；两种语言分别写自然的标题。
- `translationKey`：双语对应关系的稳定标识，两种语言必须完全相同。
- `summary`、`description`：列表摘要或页面元描述，只有在两种语言都能提供等价内容时使用。
- `draft: false`：页面准备发布时显式设置；草稿不能误进入发布内容。
- `layout`：仅在需要现有专用布局时指定，例如 `breaking-news`、`publication-index` 或 `gallery`。
- `weight`：同级页面的排序；使用现有栏目约定，避免用日期或文件名暗中承担菜单排序。
- `date`：需要日期的记录页使用 ISO 可解析日期，并保持中英文一致。

示例中的 `events`/“活动”只是中性栏目名称，不代表站点已有活动内容：

```markdown
---
title: "Events"
translationKey: events
summary: "Events and related notices."
draft: false
---

<!-- Add approved English content here. -->
```

```markdown
---
title: 活动
translationKey: events
summary: 活动及相关通知。
draft: false
---

<!-- 在此添加已核准的中文内容。 -->
```

注释只是占位说明；发布前必须替换为与另一语言等价的真实内容，不要提交空栏目冒充完成页面。

## 新增一个栏目：完整步骤

以下以 `events`（中文显示为“活动”）为例。步骤中的内容必须来自已批准材料，示例不构成实际站点内容。

### 1. 先核对范围和 URL

1. 阅读 `AGENTS.md`、`DESIGN.md`，检查现有栏目和旧站快照中是否已有相应路径。
2. 选择 lowercase slug：`events`，避免空格、大写、中文目录名和同义重复路径。
3. 如果这是现有栏目改名或迁移，先决定 URL 兼容方案。当前 `disableAliases: true`，不能在未决策时宣称旧 URL 会自动跳转。

### 2. 创建成对的栏目首页

创建完全相同的相对路径：

```text
site/content/en/events/_index.md
site/content/zh/events/_index.md
```

分别使用以下可复制 front matter；两文件的 `translationKey` 必须都是 `events`：

```markdown
---
title: "Events"
translationKey: events
summary: "Events and related notices."
draft: false
---

Approved English introduction for this section.
```

```markdown
---
title: 活动
translationKey: events
summary: 活动及相关通知。
draft: false
---

经核准的中文栏目介绍。
```

写入真实内容时逐段对齐事实、链接和限定语；不要用机器迁移结果代替人工核对。栏目没有内容时，应先保留为草稿或不要加入导航。

### 3. 在两种语言的 `hugo.yaml` 菜单中加入入口

菜单是按语言分别定义的，必须同时修改 `languages.zh.menus.main` 和 `languages.en.menus.main`。保持相同的 `pageRef` 和排序意图，使用各自语言的 `name`。例如可复制以下片段，并把 `weight` 调整到经过确认的位置：

```yaml
languages:
  zh:
    menus:
      main:
        - name: 活动
          pageRef: /events
          weight: 90
  en:
    menus:
      main:
        - name: Events
          pageRef: /events
          weight: 90
```

实际合并时不要重复添加 `languages:` 或覆盖已有菜单；把条目插入当前两个 `main` 列表。`pageRef: /events` 指向同一个翻译关联的内容页面，语言上下文决定最终链接为 `/events/` 或 `/zh/events/`。

### 4. 选择默认 layout 或现有专用 layout

先用默认行为，只有页面结构确实需要特殊数据或组件时才选择专用 layout：

- 栏目首页（`_index.md`）通常是 **list** 页面。`site/layouts/_default/list.html` 输出标题、栏目内容和 `.Pages` 列表；适合普通栏目及其子页面。
- 普通内容页（`page.md`）通常是 **single** 页面。`site/layouts/_default/single.html` 输出标题、日期和正文；适合不需要特殊字段的文章。
- `site/layouts/_default/home.html` 只用于首页 kind，不是普通栏目替代品。
- 自定义 layout 由 front matter 的 `layout` 指定，或由 Hugo 的栏目模板查找规则命中。它不是“更好看的 default”，而是对数据字段、内容结构或导航有明确要求的专用渲染器。

当前仓库已有专用模板，包括：`research/list.html`、`news/breaking-news.html`、`news/all-news.html`、`publications/publication-index.html`、`publications/full-list.html`、`publications/theses.html`、`publications/highlights.html`、`people/list.html`、`people/limei-xu.html`、`photos/list.html`、`photos/gallery.html`、`teaching/list.html`、`teaching/single.html` 和 `contact/list.html`。例如 `publication-index` 依赖子页面及其 `TranslationKey` 来查找本地化摘要，`gallery` 依赖 `Params.gallery` 与 `hugo.Data.photos`，不能只改一个 front matter 就套用。

新增栏目若只是 Markdown 和子页列表，不要复制专用模板；省略 `layout` 使用默认 list/single。若确需新布局，先确认数据契约，再在 `site/layouts/` 中实现，并保持 `baseof.html` 的页面外壳、canonical、hreflang、fingerprinted 资源和可访问性结构。

### 5. 添加子页面

普通子页面放在同一栏目目录中，并在两种语言创建对应文件：

```text
site/content/en/events/first-event.md
site/content/zh/events/first-event.md
```

两者使用相同的相对 slug、相同的 `translationKey`，并根据需要设置一致的 `date`、`weight`、`draft`。如果需要年度或层级栏目，继续使用目录和 `_index.md`，例如 `events/2026/_index.md`；每一个可见层级都要评估中英文是否都有对应页面和导航。

### 6. 添加栏目资源

- 当前项目的共享图片、PDF 等媒体统一放在 `site/static/media/`，并以 `/media/...` URL 引用；不要重复复制同一文件。
- 如果确实需要引入 Hugo page bundle 资源，先确认模板读取方式、双语目录结构和 Boda release 输出都已验证；不要在没有明确需求时混用两套资源约定。
- 模板需要的数据放入 `site/data/`，并按现有 YAML/JSON 结构读取；资源本身不要伪装成 data。
- 可由 Hugo Pipes 处理的 CSS、JavaScript 等源文件放在 `site/assets/`，通过 `resources.Get` 使用。不要把需要 fingerprint/minify 的文件放进 `static/`。

加入图片后为两种语言提供等价的 alt/caption；不要凭文件名推断图中科学含义。

## 模板、短代码与资源边界

### 模板层次

`site/layouts/_default/baseof.html` 是共同 HTML 外壳，负责语言属性、description、title、canonical、hreflang、CSS/JavaScript 资源以及 header/footer。各页面模板通过 `{{ define "main" }}` 填充内容。默认 `list.html` 和 `single.html` 的差异是页面 kind 和内容形态，不是语言差异：list 展示栏目正文加子页面列表，single 展示单页标题、日期和正文。

栏目专用 layout 只处理该栏目自己的字段和结构；共享 header、footer、breadcrumbs 应继续使用现有 partial。现有 shortcodes 为 `research-story`、`research-highlight`、`news-row`，它们分别提供研究故事、研究亮点和新闻行的结构化渲染。使用短代码前先读取对应 `site/layouts/shortcodes/*.html`，按参数契约传值；不要用短代码承载未经核实的科学内容，也不要为普通段落新造短代码。

### `static/media`、`data`、`assets` 的区别

| 位置 | 作用 | 构建行为 | 典型引用 |
| --- | --- | --- | --- |
| `site/static/`（包括 `static/media/`） | 已准备好的公开文件 | 原样复制到输出目录，不经 Hugo Pipes | `/media/example.pdf` |
| `site/data/` | 模板消费的结构化或集中维护数据 | 不直接成为公开 URL，由模板以 `hugo.Data.*` 读取 | `hugo.Data.people` |
| `site/assets/` | 需要构建处理的源资源 | 可 `minify`、`fingerprint`，并由 Hugo 生成带 hash 的 URL | `resources.Get "css/main.css"` |

需要由模板读取并 `markdownify` 的 Markdown 资源应放在 `site/assets/`，而不是 `site/data/`。当前实例是 `site/assets/data/full-publication-list.md`，模板通过 `resources.Get "data/full-publication-list.md"` 读取。

`site/public/` 和 `dist/boda-site/` 都是输出，不应手工修改后当作源代码提交。修改数据时同时检查所有读取它的模板及中英文呈现逻辑。

## 修改设计的流程

1. 先在 `DESIGN.md` 确认目标组件、颜色 token、排版、布局、交互和可访问性要求；不要先凭截图直接改 CSS。
2. 若需要新 token，先更新 `DESIGN.md` 的规范，再在 `site/assets/css/main.css` 的 `:root` 变量中实现；优先复用现有 `--accent`、`--secondary`、`--ink`、`--muted`、`--line` 等 token。
3. 修改对应模板或 partial，使语义结构、标题层级、链接名称和图片 alt 正确；不要用 CSS 掩盖错误的 HTML 或内容结构。
4. 为窄屏检查 `@media` 规则，确保无页面级横向滚动、导航可用、正文仍易读，且 body 文本不低于规范要求。
5. 检查键盘焦点、跳过链接、语义 landmarks、表单/链接名称、图片 alt 和 `prefers-reduced-motion`。颜色不能成为传达类别或状态的唯一方式。
6. 预览并按本文末尾清单验证后再构建发布候选。

### Hugo fingerprint 与 Boda release

`baseof.html` 通过 `resources.Get "css/main.css" | minify | fingerprint` 和对应的 JavaScript 管道生成带 fingerprint 的 URL，并在 HTML 中加入 `integrity="sha256-..."`。这适合普通 Hugo 输出，可缓存并检测资源篡改。

Boda 上传 CSS 和 JavaScript 时会前置 UTF-8 BOM，字节改变后原来的 SRI hash 不再匹配，浏览器会拒绝资源。因此发布候选必须使用 `tools/build_boda_release.sh`：它在生产构建后移除 HTML 中的 `integrity` 属性，并检查发布目录不含开发 URL、VSB 引用、Boda 不接受的文件名和残留 `integrity`。不要手工在 `site/public/` 删除属性，也不要把 Boda 的处理反推回 Hugo 模板。

## 本地预览、构建与发布构建

从仓库根目录执行：

```sh
# 本地预览，监听 site/ 的改动
hugo server --source site

# 普通构建，输出到 site/public/
hugo --source site --cleanDestinationDir

# 生产 Boda 发布候选，输出到 dist/boda-site/
tools/build_boda_release.sh

# 只读规划和会话探测（发布前）
python3 -m pip install -r boda_release/requirements.txt
tools/bodacli plan dist/boda-site
tools/bodacli probe
```

`tools/build_boda_release.sh` 使用生产环境、正式 `baseURL`，并生成 `SHA256SUMS`；它还删除默认语言可能产生的 `/en/` 目录，并复制一致的 `index.htm`。需要目录前缀时设置 `BODA_PATH_PREFIX=/new` 或 `/trial/site`，不要直接改 `hugo.yaml` 的 `baseURL`。

实际部署是立即写入远端的操作。只有完成审批、回滚材料和发布前检查后，才按 `BODA_DEPLOYMENT.md` 的约束执行：

```sh
tools/bodacli deploy dist/boda-site --apply --confirm DEPLOY_NONATOMIC
```

默认不需要设置 `BODA_SECURITY_REASON`；如需提供自定义的非秘密审核说明，可在命令前临时设置该环境变量。具体生产操作以 [`operator-guide.md`](operator-guide.md) 为准。

### 增量发布的输出边界

`tools/bodacli deploy dist/boda-site --incremental --apply --confirm DEPLOY_INCREMENTAL` 仍以一次完整 Hugo build 为前提。构建脚本生成本地 `BODACLI_BUILD.json`，记录构建时 commit/dirty 状态；该文件不进入 `SHA256SUMS`、不上传，CLI 会拒绝与当前工作区不匹配的旧 artifact。Hugo fan-out 可能把一个源变更展开为多个 HTML、资源或索引输出；因此上传选择必须来自完整构建产物的 SHA-256 manifest diff，而不是“修改的页面”列表。`git diff` 只验证 commit 祖先关系并提供源变更审计，不能直接映射 Hugo 输出。

首次没有 `bodacli-state.txt` 时，增量部署执行全量 bootstrap。该 TXT 文件承载 canonical JSON state。所有部署都要求当前 Git 工作区干净，并拒绝 dirty 或与当前工作区不匹配的 artifact。state 仅含 schema、commit、dirty、path_prefix 和生成文件 SHA-256 清单，不含源码或凭据。state 损坏、路径不符、commit 非祖先、dirty 基线、远端内容漂移或运行中 state 变化时必须 fail-closed。删除仅限旧 state 声明且 checksum 仍匹配的文件，不自动删除目录；删除后还要以独立 cache-buster 确认连续公开 404，才可最后写 state。Boda 无原子 compare-and-swap，手动部署不得并发。普通 full deploy 仍使用 `DEPLOY_NONATOMIC`，普通/增量失败都可能留下非原子混合版本。

不要运行 `tools/migrate_english.py`。它只记录早期批量引导，会重写英文 Markdown、data 和本地 media；维护站点时必须对照只读快照，逐页人工编辑。

## 发布前验证清单

### 页面与路由

- [ ] 桌面宽度下首页、栏目页、子页面和 404 均能打开，标题、canonical、hreflang 正确。
- [ ] 移动宽度下无文档级横向滚动；导航、图片、表格和长链接可用。
- [ ] 英文根路径与中文 `/zh/` 路径均可访问；语言切换指向对应 `translationKey` 页面。
- [ ] 新增栏目 slug 全部 lowercase；中英文 `_index.md`、子页和菜单都已成对更新。
- [ ] 外链、站内链接、PDF、图片和菜单 `pageRef` 都没有 404；相对路径没有误指向 `/en/`。
- [ ] 如果改变了已有 URL，已先记录并决定兼容策略；没有把 `disableAliases=true` 下的自动兼容当成事实。

### 交互与可访问性

- [ ] 只用键盘 Tab/Shift+Tab 可到达菜单、语言切换、正文链接和控件，焦点清晰可见。
- [ ] 跳过链接可直达 `#main`；标题层级和 landmark 结构合理。
- [ ] 图片有准确 alt；装饰图才使用空 alt；链接名称能说明目的。
- [ ] hover、active、focus 状态可辨识，不依赖颜色作为单一方式；窄屏菜单和 `prefers-reduced-motion` 行为正常。

### 双语与内容

- [ ] 中文和英文事实、主张、限定语、日期、链接、人物和栏目覆盖等价。
- [ ] front matter 的 `translationKey` 成对且稳定；未完成翻译没有进入生产导航。
- [ ] 内容只来自已批准材料；没有从 `source/xulm.pku.edu.cn/` 推断科学内容、人物或经历。
- [ ] 没有运行 `tools/migrate_english.py`，也没有手改生成目录冒充源文件。

### 发布输出

- [ ] 已用普通 `hugo` 或 `tools/build_boda_release.sh` 重新生成输出，而不是上传 `hugo server` 产物。
- [ ] Boda 候选目录无 `localhost`、`127.0.0.1`、`livereload`、`.vsb` 和 `integrity` 属性。
- [ ] `index.html` 与 `index.htm` 字节一致，`SHA256SUMS` 已生成；文件名符合 Boda 限制。
- [ ] 发布前已准备并核对回滚包；未在探测阶段点击全局“发布”。
