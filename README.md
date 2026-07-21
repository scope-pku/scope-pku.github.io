# SCOPE Group Web

**简体中文** | [English](README_en.md)

北京大学 SCOPE 研究组的双语 Hugo 网站。生产站点默认通过 GitHub Pages 自动部署，
同时保留一个用于备用静态托管和应急发布的 Boda V12 Python 客户端。

## 项目特点

- 双语 Hugo 站点：英文位于 `/`，中文位于 `/zh/`。
- 提供研究、成果、成员、新闻、照片、教学和联系方式等学术内容页面。
- 通过共享内容和数据约定，保持中英文页面信息等价。
- 使用 `uv` 和 `uv.lock` 管理可复现的 Python 工具环境。
- 默认生产发布使用 GitHub Pages；Boda 作为备用和应急发布入口保留。

## 快速开始

### 环境要求

请先安装：

- [Hugo Extended](https://gohugo.io/installation/)
- 如需使用 Boda CLI 或运行 Python 测试，请安装
  [uv](https://docs.astral.sh/uv/getting-started/installation/)

在 macOS 上可以直接运行：

```sh
brew install hugo
curl -LsSf https://astral.sh/uv/install.sh | sh
```

确认工具已经安装：

```sh
hugo version
uv --version
```

推荐使用 Hugo Extended，因为网站通过 Hugo Pipes 处理 CSS 和 JavaScript
资源。Python 包要求 Python 3.13 或更高版本；需要时 uv 可以自动安装和管理
对应的 Python 版本。

### 本地预览

在仓库根目录运行：

```sh
hugo server --source site
```

打开 Hugo 输出的本地地址，通常为 <http://localhost:1313/>。英文站点位于
`/`，中文站点位于 `/zh/`。源文件发生变化后，Hugo 会重新构建并刷新浏览器。

如需同时预览草稿和未来日期的页面：

```sh
hugo server --source site --buildDrafts --buildFuture
```

使用 `Ctrl-C` 停止服务器。

### 生产构建

在仓库根目录生成生产版本：

```sh
hugo --source site --minify
```

静态输出位于 `site/public/`。不要部署 `hugo server` 生成的开发输出；GitHub Pages
会在推送到 `main` 后自动完成生产构建和部署。仅在备用或应急场景下，才使用下文所述
的 Boda 发布构建工具。

## 常用命令

```sh
# 预览 Hugo 网站。
hugo server --source site

# 生成压缩后的生产版本。
hugo --source site --minify

# 安装 Boda CLI 的锁定运行依赖。
uv sync --locked --no-dev

# 安装锁定的开发依赖并运行全部 Python 测试。
uv sync --locked --dev
uv run pytest tests

# （备用/应急）构建并检查 Boda 发布产物。
tools/build_boda_release.sh
tools/bodacli plan dist/boda-site
tools/bodacli probe
```

只有连接 Boda 的操作才需要认证信息。不得提交用户名、密码、OTP 种子、会话
Cookie 或未完成的私有材料。上传内容可能立即公开；执行任何写操作前必须阅读
运营者指南。

## 项目结构

```text
.
├── site/                    # Hugo 源码及生成的 public/ 输出
│   ├── content/en/          # 英文内容，对应 /
│   ├── content/zh/          # 中文内容，对应 /zh/
│   ├── layouts/             # Hugo 模板和短代码
│   ├── assets/              # Hugo Pipes 源资源
│   ├── static/              # 原样复制到公开站点的文件
│   ├── data/                # 成员、照片和联系方式等共享数据
│   ├── i18n/                # 界面翻译
│   └── hugo.yaml            # Hugo 和语言配置
├── bodacli/                 # Boda V12 Python 客户端
├── tools/                   # 发布工具和 CLI 入口
├── tests/                   # Python CLI 与部署测试
├── docs/                    # 开发、运营和内容维护文档
├── pyproject.toml           # Python 项目与依赖组配置
└── uv.lock                  # 锁定的 Python 依赖解析结果
```

可选目录 `source/xulm.pku.edu.cn/` 是旧公开站点的本地不可变快照。该目录只供
核对，不能修改，并且不会进入 Git。

## 贡献与内容开发

提交 Issue 或 Pull Request 前，请先阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)，其中包含提交条件、Issue checklist、PR checklist 以及验证要求。

修改公开内容、模板、样式或组件前，请先阅读：

- [`AGENTS.md`](AGENTS.md)：仓库规则和部署边界。
- [`CONTRIBUTING.md`](CONTRIBUTING.md)：Issue、PR、验证和协作流程。
- [`DESIGN.md`](DESIGN.md)：视觉、编辑、双语和无障碍要求。
- [`docs/developer-guide.md`](docs/developer-guide.md)：Hugo 数据模型、模板、
  构建检查和验证流程。
- [`docs/content-update-examples.md`](docs/content-update-examples.md)：常见内容
  修改的可复制示例。

双语页面应在 `site/content/en/` 和 `site/content/zh/` 中使用相同的相对路径
和 `translationKey`。两种语言中的事实、主张、限定语、链接、人物和日期必须
等价，但不要求逐句直译。

## 文档索引

- [`site/README.md`](site/README.md)：Hugo 内容和预览的简要说明。
- [`docs/developer-guide.md`](docs/developer-guide.md)：开发流程、架构和验证方法。
- [`docs/content-update-examples.md`](docs/content-update-examples.md)：各类页面的
  内容维护示例。
- [`docs/operator-guide.md`](docs/operator-guide.md)：GitHub Pages 生产发布说明，以及
  Boda 备用入口的操作、认证、探测、部署和回滚。
- [`BODA_DEPLOYMENT.md`](BODA_DEPLOYMENT.md)：部署安全规则和发布协议。

## GitHub Pages

推送到 `main` 后，GitHub Actions 会将 Hugo 网站部署到
<https://scope-pku.github.io/>。工作流会构建 `site/` 并部署生成的产物，
不需要提交 `site/public/`。CI 细节请查看仓库设置和工作流文件。

## 部署边界

正常生产发布通过 GitHub Actions 完成：合并或推送到 `main` 后，`.github/workflows/pages.yml`
会构建并部署 GitHub Pages。不要手工上传 `site/public/`，也不要为普通 PR 执行生产部署。

Boda 是备用和应急入口，不是默认发布路径。Boda 部署属于生产写操作，即使目标目录没有
公开链接，或名称中包含“测试”“探测”等字样，也不能视为安全沙箱。需要使用 Boda 时，
先阅读运营文档，构建产物并运行只读的 `plan` 和 `probe`，取得明确授权后再进行部署。
