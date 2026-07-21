# 文档索引

本目录按任务组织 SCOPE Group Web 的开发、内容维护和生产运营文档。新贡献者先阅读
根目录 [`README.md`](../README.md) 和 [`CONTRIBUTING.md`](../CONTRIBUTING.md)，
再根据当前任务进入对应指南。

## 从这里开始

| 我要做什么 | 首先阅读 | 继续阅读 |
| --- | --- | --- |
| 在本地运行或修改 Hugo 网站 | [`developer-guide.md`](developer-guide.md) | [`../DESIGN.md`](../DESIGN.md) |
| 更新新闻、论文、成员、照片或教学内容 | [`content-update-examples.md`](content-update-examples.md) | [`developer-guide.md`](developer-guide.md) |
| 提交 Issue 或 Pull Request | [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | [`../AGENTS.md`](../AGENTS.md) |
| 查看默认生产发布 | [`operator-guide.md`](operator-guide.md) | 仓库 `.github/workflows/pages.yml` |
| 构建或检查 Boda 备用产物 | [`operator-guide.md`](operator-guide.md) | [`../BODA_DEPLOYMENT.md`](../BODA_DEPLOYMENT.md) |
| 执行 Boda 备用部署或回滚 | [`../BODA_DEPLOYMENT.md`](../BODA_DEPLOYMENT.md) | [`operator-guide.md`](operator-guide.md) |

## 文档职责

### 开发与内容

- [`developer-guide.md`](developer-guide.md)：Hugo 目录、双语路由、front matter、
  模板、样式、资源、构建方式和本地验证。
- [`content-update-examples.md`](content-update-examples.md)：新闻、研究亮点、研究主题、
  论文列表、成员、照片和教学内容的最小可复制示例。
- [`../DESIGN.md`](../DESIGN.md)：网站视觉、编辑语气、双语等价、组件和无障碍规范。

### 贡献与协作

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md)：Issue 与 Pull Request 流程、提交前检查、
  验证要求和 checklist。
- [`../AGENTS.md`](../AGENTS.md)：仓库范围、协作约束和不可越过的安全边界。

### 发布与运营

- `.github/workflows/pages.yml`：默认生产发布；推送到 `main` 后自动构建并部署 GitHub Pages。
- [`operator-guide.md`](operator-guide.md)：GitHub Pages 发布说明，以及 Boda 备用入口的
  安装、认证、只读探测、发布候选、部署步骤、故障处理和发布后检查。
- [`../BODA_DEPLOYMENT.md`](../BODA_DEPLOYMENT.md)：生产发布协议、确认令牌、增量状态、
  回滚和平台限制，是部署操作的最终依据。

## 文档维护原则

- 根 `README.md` 只保留项目定位、快速开始、常用命令和文档入口。
- 开发实现细节放入 `developer-guide.md`，内容配方放入
  `content-update-examples.md`。
- 贡献流程只在 `CONTRIBUTING.md` 中定义，Issue 与 PR 模板引用该流程。
- 生产操作和凭据规则只在运营文档中展开，不复制到普通开发教程。
- 修改命令、路径或发布行为时，同步检查所有引用该事实的文档链接。

> GitHub Pages 是默认生产发布路径。Boda 上传可能立即形成生产写入；没有明确授权时，
> 只能执行本地构建和文档中标记为只读的检查，不得把未完成内容上传到任何远端目录。
