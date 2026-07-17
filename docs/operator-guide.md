# 运营者指南

本文面向负责构建、检查、部署和回滚网站的运营者。所有命令均从仓库根目录执行；不要把本指南中的示例凭据替换后提交到 Git。

## 1. 职责与立即公开风险

运营者负责：

- 从已审核的 Git 提交构建可部署的 Hugo release；
- 在写入 Boda 前完成计划检查、会话探测和必要的 CRUD smoke；
- 确认发布路径、回滚材料、公开校验和部署后的页面；
- 记录部署原因、异常和回滚决定。

Boda 的静态文件上传是**立即公开的生产写入**，不需要点击全局“发布”。未链接目录、目录名含“未发布”或其他隐蔽命名都不是访问控制。探测时也不要点击全局“发布”，不要上传私料、密钥、未完成的私有材料。

首次切换前必须准备网站包回滚材料。Boda 网站包导入会覆盖当前站点并清空全文索引；Hugo ZIP 不是网站包，禁止把它当作网站包导入。

## 2. 安装客户端依赖

在仓库根目录执行：

```sh
python3 -m pip install -r boda_release/requirements.txt
```

正式入口是 `tools/bodacli`。它会切换到仓库根目录并调用 `python3 -m boda_release`；不要使用旧的兼容 wrapper。

依赖包括 `requests`、`pyotp` 和 `cryptography`。构建 release 还需要当前项目使用的 Hugo，以及构建脚本调用的 `rg`、`find`、`sed`、`cmp` 等命令。

## 3. 认证、`.env` 与文件权限

客户端从进程环境读取认证值；若环境中没有该值，则读取仓库根目录 `.env`：

- `BODA_IAAA_USERNAME`
- `BODA_IAAA_PASSWORD`
- `BODA_IAAA_OTP`（可选，但 IAAA 要求二次验证时必须提供）
- `BODA_SESSION_FILE`（可选；未设置时使用操作系统/XDG 缓存目录中的 `bodacli/session.cookies`，macOS 默认为 `~/Library/Caches/bodacli/session.cookies`，Linux 默认为 `~/.cache/bodacli/session.cookies`）
- `BODA_BASE_URL`（可选，默认 `https://boda.pku.edu.cn`）
- `BODA_PUBLIC_URL`（可选，默认 `https://xulm.pku.edu.cn`）
- `BODA_PATH_PREFIX`（可选，见下文）
- `BODA_SECURITY_REASON`（可选；未设置时 CLI 自动生成带 UTC 时间的非秘密原因，设置时用于结构化 receipt 的文件安全记录）

`.env` 使用简单的 `KEY=value` 行；进程环境优先于 `.env`。值可以用一对单引号或双引号包住。不要在文档、日志、提交、工单或截图中写入真实用户名、密码、OTP、cookie 或 session 内容。

```sh
chmod 600 .env
```

客户端登录成功后会自动在用户缓存中保存并复用持久会话 cookie；会话过期时会重新走 IAAA 登录。客户端会创建缓存目录并强制 session 文件为 `0600`，无需人工维护。`BODA_SESSION_FILE` 仅用于高级覆盖；不要复制、提交或记录 session 内容。

### OTP 的三种格式

`BODA_IAAA_OTP` 支持以下任一种格式：

1. Base32 TOTP seed；
2. `otpauth://` URI；
3. 已生成的六位一次性数字验证码。

验证码必须在登录时有效；不要把真实 seed、URI 或验证码写入 shell 历史、文档或代码。若使用六位码，过期后重新生成；不要把过期验证码当作长期配置。

## 4. 构建 release 与路径前缀

### 根路径构建

`BODA_PATH_PREFIX` 为空或 `/` 表示站点根路径：

```sh
BODA_PATH_PREFIX= tools/build_boda_release.sh
./tools/bodacli plan dist/boda-site
```

构建结果位于 `dist/boda-site/`，包含 `SHA256SUMS`。构建器会清理 `en/`、生成相同的 `index.html` 与 `index.htm`、移除 HTML 中的 `integrity` 属性，并拒绝开发地址、VSB 引用和 Boda 不接受的文件名。

### `/new` 构建

```sh
export BODA_PATH_PREFIX=/new
tools/build_boda_release.sh
./tools/bodacli plan dist/boda-site
```

`BODA_PATH_PREFIX` 必须同时用于**构建和上传**。构建时它传给 Hugo 的 `--baseURL`；上传时它决定 Boda 目标根目录和公开校验路径。不能用 `/new` 构建后以根路径上传，也不能用根路径构建后上传到 `/new`。支持类似 `/trial/site` 的安全路径段；不要使用含空格或其他不安全字符的前缀。

上传时可显式传递相同前缀，避免依赖当前 shell：

```sh
./tools/bodacli deploy dist/boda-site \
  --path-prefix /new \
  --apply --confirm DEPLOY_NONATOMIC
```

`BODA_SECURITY_REASON` 可用于覆盖 CLI 自动生成的非秘密原因；若设置，生产操作应使用经过审核的原因文本，不要把用户名、密码或 OTP 放入其中。

## 5. 发布前的 plan、probe 与 CRUD smoke

### `plan`（只读）

```sh
./tools/bodacli plan dist/boda-site
```

`plan` 读取并验证 `SHA256SUMS`、实际文件集合、每个文件 SHA-256，以及相同的 `index.html`/`index.htm`；同时输出将要处理的文件。失败时不得继续部署。

### `probe`（只读远端检查）

```sh
./tools/bodacli probe --path-prefix /new
```

`probe` 验证 Boda 会话和目标根目录，不上传文件。若使用根路径，省略 `--path-prefix` 或设置为空。它不会替代发布后的 HTTP 检查。

### CRUD smoke

固定 smoke 命令：

```sh
./tools/boda_crud_test.sh
```

它等价于对 `--path-prefix /test` 执行 `crud-test --apply --confirm BODA_CRUD_TEST`，实际写入并验证 `/test/A/B.txt`，随后删除文件和目录。若 `/test/A` 已存在，测试会拒绝运行；不要预先创建它。CRUD smoke 不可与另一个 CRUD smoke 或部署并发，因为它使用固定路径并会删除 `A`。

## 6. 部署 `/new`、根路径与双重确认

部署是非原子操作：远端可能在上传过程中短暂呈现混合版本。正式部署前要先完成 `plan`、`probe`、回滚材料检查和（需要时）CRUD smoke。

### `/new` 示例

```sh
export BODA_PATH_PREFIX=/new
tools/build_boda_release.sh
./tools/bodacli plan dist/boda-site
./tools/bodacli probe --path-prefix /new
./tools/bodacli deploy dist/boda-site \
  --path-prefix /new \
  --apply --confirm DEPLOY_NONATOMIC
```

### 根路径示例

```sh
export BODA_PATH_PREFIX=
tools/build_boda_release.sh
./tools/bodacli plan dist/boda-site
./tools/bodacli probe
./tools/bodacli deploy dist/boda-site \
  --apply --confirm DEPLOY_NONATOMIC
```

`BODA_SECURITY_REASON` 是可选的非秘密审查原因；未设置时 CLI 自动生成带 UTC 时间的原因，设置时不得为空白或包含换行。上传可能返回结构化 receipt，客户端必须据此执行 security update，并检查 Boda 返回的固定响应。服务端也可能返回**精确的纯文本 `ok`**；这种响应没有安全字段，客户端只接受字节完全相同的 `ok`，随后必须用公开 URL 的 SHA-256 校验确认内容。其他非 JSON、非精确 `ok` 响应都应视为失败，不要盲目重试。
双重确认包括：

1. CLI 必须同时收到 `--apply` 和精确的 `--confirm DEPLOY_NONATOMIC`；缺一不可；
2. 运营者必须在发布记录/审批流程中确认这是已审核的生产写入，并确认回滚材料可用。

GitHub Actions 只负责在 `main` 上构建并校验固定 `/new` 的 release artifact；Boda 登录和上传始终在本地执行。GitHub-hosted runner 无法连接 Boda CAS handoff，因此不得把 Boda 凭据重新放入 GitHub Secrets，也不得把远端 workflow 改回直接上传。

### GitHub 封包与本地一键部署

远端 `Boda release package` workflow 通过 `workflow_dispatch` 手动触发。它执行生产 Hugo 构建、`bodacli plan` 和 artifact 上传，artifact 名为 `boda-site-<commit>`，保留三天。它不登录 Boda，也不读取 Boda credentials。

仓库是 public，但触发 workflow 和下载 artifact 仍需要本地 GitHub token。设置 `GITHUB_TOKEN`（或 `GH_TOKEN`）；fine-grained token 应仅授权 `scope-pku/scope-pku.github.io`，权限为 **Actions: read and write**、**Contents: read**。classic PAT 只需要 `repo` scope。token 只保存在本地进程环境，不要写入命令参数、`.env`、GitHub Secrets、日志或文档。

token 已导出后，先把部署脚本完整下载到权限受限的临时文件；只有 curl 成功才交给 `sh`。以下命令执行默认 full deploy，并通过 `/dev/tty` 要求输入 `DEPLOY_NONATOMIC`：

```sh
deploy_script=$(mktemp)
chmod 600 "$deploy_script"
trap 'rm -f "$deploy_script"' 0 HUP INT TERM
printf 'Authorization: Bearer %s\n' "$GITHUB_TOKEN" \
  | curl --fail --silent --show-error --location --connect-timeout 15 --max-time 300 --header @- \
      --header 'Accept: application/vnd.github.raw+json' \
      --output "$deploy_script" \
      https://api.github.com/repos/scope-pku/scope-pku.github.io/contents/tools/deploy_github_release.sh \
  && sh "$deploy_script"
```

这种写法通过 curl 的标准输入传递 Authorization header，token 不会出现在 curl 参数列表中；下载失败或中断时不会执行不完整脚本。若使用 `GH_TOKEN`，把命令中的 `$GITHUB_TOKEN` 换成 `$GH_TOKEN`。

此命令会自动：

1. 使用 GitHub REST API 触发 `boda-release.yml` 的 `main` 手动构建并轮询至完成；
2. 精确下载 `boda-site-<commit>` artifact，并核对 run、branch、event、commit 与构建 metadata；
3. 如果当前目录是本仓库，创建临时 detached worktree；否则通过临时 `GIT_ASKPASS` 私密 clone，并 checkout artifact 的 exact commit；
4. 创建临时 Python virtual environment，安装该 commit 的 Boda CLI dependencies；
5. 以固定 `BODA_PATH_PREFIX=/new` 执行 plan 和本地 Boda probe；
6. 显示 run URL、commit 和模式，要求精确确认令牌后才执行 deploy；
7. 结束后删除 artifact、virtual environment、临时 clone/worktree 和 askpass 文件。

本机只需 `curl`、`git` 和 `python3`，不需要 `gh`、Hugo、ripgrep 或预装的 Boda dependencies。Boda credentials 继续使用进程环境、当前仓库/目录的 `.env`，或由 `BODA_ENV_FILE=/absolute/path/to/.env` 指定；凭据文件必须为 `0600` 且不得提交。

若已 checkout 仓库，也可直接运行同一脚本：

```sh
./tools/deploy_github_release.sh
```

常用安全模式可把选项传给已下载的临时脚本：

```sh
# 只构建、下载并验证 artifact
sh "$deploy_script" --plan-only

# 本地 probe、增量同步或指定现有 run
sh "$deploy_script" --probe-only
sh "$deploy_script" --incremental
sh "$deploy_script" --run-id RUN_ID

# 已 checkout 仓库时也可直接运行
./tools/deploy_github_release.sh --plan-only
```

无人值守调用可传入 `--confirm DEPLOY_NONATOMIC`，增量模式使用 `--incremental --confirm DEPLOY_INCREMENTAL`，但只能在已有外部审批和日志记录时使用。默认等待 GitHub workflow 最多 1800 秒，单个 GitHub API 请求最多 300 秒；需要调整时使用 `BODA_RELEASE_TIMEOUT_SECONDS`、`BODA_RELEASE_POLL_SECONDS` 和 `BODA_RELEASE_REQUEST_TIMEOUT_SECONDS`。

`--plan-only`、`--probe-only` 和 `--incremental` 的互斥组合及错误参数会 fail-closed。full deploy 不删除远端多余文件；incremental 只允许删除旧 state 管理且 checksum 仍匹配的文件，但两者都会立即公开写入 `/new`，并且都不是原子操作。不要并发运行本地部署，也不要在未核对回滚材料时输入确认令牌。

部署实现先按“浅目录到深目录”创建缺失目录，再上传全部 release 文件；根 `index.html` 和 `index.htm` 排在最后。所有上传结束后才统一进行公开 URL SHA-256 校验。校验最多尝试 5 次，每次失败间隔 1 秒。CSS/JS 的公开内容会去除 Boda 注入的 UTF-8 BOM 后再与本地 SHA-256 比较。

普通 full deploy 上传完整 release，成功后刷新 state，但不删除远端多余文件。增量 deploy 只删除旧 state 声明且公开 checksum 仍匹配的文件；不自动删除目录或未由旧 state 管理的文件。普通和增量部署都不是原子操作，失败可能留下混合版本。

## 6.1 增量部署与状态协议

增量命令仍先完整构建 Hugo，再比较完整 `dist/boda-site/` 输出的 SHA-256 manifest：

```sh
export BODA_PATH_PREFIX=/new
tools/build_boda_release.sh
./tools/bodacli deploy dist/boda-site \
  --incremental --apply --confirm DEPLOY_INCREMENTAL
```

Hugo fan-out 可能让一次源代码变更生成多个输出文件，因此不能按 `git diff` 推断上传页；Git diff 只用于 commit 祖先关系验证和源变更审计。构建脚本会生成仅供本地校验、不会上传的 `BODACLI_BUILD.json`；其 commit/dirty 状态与当前工作区不一致时，部署会 fail-closed。没有 `bodacli-state.txt` 时，增量命令执行全量 bootstrap。state 使用 Boda 可公开提供的 TXT 文件承载 canonical JSON，仅含 schema、commit、dirty、path_prefix 和生成文件 SHA-256 清单，不含源码、凭据、cookie 或 session。

所有部署都要求执行 CLI 的 Git worktree 干净，且 `BODACLI_BUILD.json` 与其 commit/dirty 状态完全匹配；一键工具通过 artifact 对应 commit 的临时 detached worktree 满足此约束，dirty artifact 会在远端写入前被拒绝。state 损坏、路径前缀不符、commit 非祖先、基线 dirty、远端内容 checksum 漂移或部署过程中 state 被其他操作更新时，也必须 fail-closed。删除仅限旧 state 管理且 checksum 仍匹配的文件；不删除目录。每个删除都必须同时通过管理端 listing 和带独立 cache-buster 的连续公开 404 校验，随后才最后写 state。Boda 不提供原子 compare-and-swap，因此本地部署不得并发；GitHub concurrency 只串行生成封包，不能锁定本地 deploy。增量双确认令牌是 `DEPLOY_INCREMENTAL`；普通 full deploy 仍使用 `DEPLOY_NONATOMIC`。

## 7. 发布后清单

- [ ] 确认部署命令成功，并记录上传文件数和 Git 提交。
- [ ] 访问根路径；`/new` 部署访问 `https://xulm.pku.edu.cn/new/`，根部署访问 `https://xulm.pku.edu.cn/`。
- [ ] 所有检查路径都相对于本次 `BODA_PATH_PREFIX`：部署到 `/new` 时检查 `/new/index.htm`、`/new/index.html`、`/new/zh/` 和 `/new/...` 资源；部署到根路径时才检查 `/index.htm`、`/index.html`、`/zh/`。
- [ ] 检查中英文切换、HTTPS、移动布局，以及带缓存破坏查询参数的 URL。
- [ ] 对失败或传播延迟保留响应状态、URL、期望 SHA-256、实际 SHA-256 和时间。
- [ ] 不因旧文件仍存在就宣称远端已完成镜像；先确认新站稳定，再安排单独清理。

## 8. 故障处理

### 认证失败

先运行只读 `probe`。若提示会话过期，确认 `BODA_IAAA_USERNAME`、`BODA_IAAA_PASSWORD`、OTP 格式和当前有效性；检查 `.env` 是否被环境变量覆盖，以及 session 文件是否可读且为 `0600`。不要把凭据复制到命令行参数或日志。当前 CLI 只支持密码和 OTP，提交的 `randCode`、`smsCode` 始终为空，不支持交互输入 CAPTCHA 或短信验证码；若 IAAA 要求这些方式，应停止自动化并由管理员或维护者确认受支持的认证路径，不能把验证码写进文档或日志。

### OTP 失败

确认是 Base32 seed、`otpauth://` URI 或当前六位码之一；检查系统时间同步，重新生成未过期验证码。不要重复使用旧码，也不要把 seed 当作六位码填写。

### receipt 或 security update 失败

结构化 receipt 必须字段完整、目标路径一致，并完成文件安全更新。非 JSON receipt、结构不符、目标路径不符或 security-update 响应校验失败都应停止；唯一例外是字节完全等于 `ok` 的 receiptless 响应，该路径仍必须通过公开 SHA-256 校验。不要把任意“成功”文字或带空白的 `ok` 当作精确 `ok`。先检查远端文件状态，再决定是否重试，避免重复写入。

### 404 或传播延迟

公开校验会对每个文件最多重试 5 次。若仍为 404，确认上传目标与公开 URL 使用同一个 `BODA_PATH_PREFIX`，目录已按浅到深创建，文件名大小写正确，并检查根入口是否为相同内容的 `index.htm` 和 `index.html`。保留失败证据；不要仅因上传接口返回成功就宣布完成。

### checksum 不匹配

确认本地 release 未被修改，重新执行 `./tools/bodacli plan dist/boda-site`；检查 `SHA256SUMS`、公开 URL、缓存破坏参数和 CSS/JS BOM 差异。若公开内容持续不匹配，停止部署并记录期望/实际摘要，不要用手工改文件绕过校验。

### 部分部署

部署非原子，部分文件已经公开时不要自动删除或强行覆盖。停止并记录已上传文件、失败文件及远端状态；从同一 release 重新执行前先确认没有错误路径或并发部署。必要时由回滚决策人使用已验证的网站包恢复，并随后重建全文索引。

## 9. 备份、回滚与全文索引

生产替换或网站包导入前：

1. 在 Boda 导出并保留原始网站包及其 companion 文件；
2. 保留对应 `SHA256SUMS`，并复制到站外第二位置；
3. 不要用通用压缩工具解包再重打包 Boda 包；保留原始字节；
4. 记下当前 Git 提交、release `SHA256SUMS`、部署路径和验证结果。

当前仓库记录的本地回滚材料位于 `backups/boda/2026-07-16/`；HTML 快照 `source/xulm.pku.edu.cn/` 仅用于对比，不是完整 CMS 回滚包。

回滚时在 Boda 执行“管理中心”→“备份恢复”→“导入导出网站包”，仅在失败证据和回滚决策人批准后导入已验证的网站包。导入覆盖当前站点并清空全文搜索索引；恢复后按 Boda 要求重建全文索引，再检查 `/`、`/index.htm`、核心栏目和静态资源。不要把 `dist/boda-site` 的 Hugo ZIP 当作网站包导入。

## 10. 禁止事项

- 禁止点击全局“发布”作为静态上传或探测步骤；
- 禁止上传真实凭据、OTP、cookie、私料或未完成私有材料；
- 禁止把 Hugo ZIP 当作 Boda 网站包导入；
- 禁止在没有可验证回滚材料和回滚路径时直接替换生产站点；
- 禁止绕过 `plan`、`probe`、双重确认、receipt/security update 或公开 SHA-256 校验；
- 禁止把一次成功的上传响应误认为整站已原子完成；
- 禁止在未评估影响的情况下删除远端多余文件。
