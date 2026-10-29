# DSH 插件方案调研与决定

**调研日期：** 2026-10-29。以下为规格阶段决定；实施时以目标 DSH 版本的源码与实测结果复核。

## 已核对的上游机制

1. DSH profile 的 bundle 通过 `package.json` 中 `dsh.bundle.patch` 声明补丁，安装后作为 profile 的一层组合配置；profile 自身和 home 级补丁可覆盖。官方 [profile 实现](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/boot/app-boot/src/profile.ts) 和 [发布指南](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/develop/basic/publish.md) 给出该契约。
2. DSH 官方 [MCP client](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md) 把一个服务实例的工具挂到 `mcp__<serverName>__<tool>`；stdio/HTTP 配置需实际挂到 patch，单纯把 `dsh-mcp-client` 包列入 bundles 不会建立连接。
3. DSH [Skill filesystem 实现](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/skill/skill-filesystem/src/index.ts) 支持 `SKILL.md` 前置信息和目录级发现；随包 Skill 也可由宿主插件注册至 `ctx.skills`，按需加载。需要实测当前 `0.1.1-rc.2` 的注册 API 与配置形态。
4. 当前本机 `dsh --version` 为 `0.1.1-rc.2`。公开文档和 GitHub `master` 比本机新，不能直接把新版本示例当作本机稳定接口；开发前固定兼容矩阵，至少验证本机版本和目标发布版本。
5. 本机 `0.1.1-rc.2` 的 `@deepseek-ai/dsh-client-ui-settings-plugins` 已提供「设置 → 插件 → 插件配置」下的 `settings.plugin.item` 扩展点，并带有 secret-role 字段经凭据域写入的模式；本机有 `dsh-credentials`/`dsh-credentials-local`，但没有 `dsh-client-ui-plugin-manager`。新版 DSH 官方 [插件管理页面](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/client/ui-plugin-manager/README.md)改用 `plugins.bundle.config` / `plugins.row.config` 扩展点；[凭据子系统](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/credentials/README.md)允许配置只保存凭据引用。需要按实际锁定版本选对应入口并做端到端运行探针；目前仅验证了包与文档存在，未验证本插件的页面注册和安全写入。
6. DSH [commands 文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/interaction/commands/README.md)说明命令不成为模型消息，但执行会写入会话日志；`recordInput:false` 只避免重复记录输入，不能据此认定携带密码的命令安全。因此完整含密码 DSN 不进入普通对话或斜杠命令。

## 方案比较

| 方案 | 优点 | 阻碍 | 决定 |
| --- | --- | --- | --- |
| 仅在 DSH 挂原项目 MCP | 最快获得工具名 | 旧 MCP 依赖 `app.main`、MySQL 和 Financial Freedom 进程/源码；不满足独立运行 | 仅作对照测试，不作为完成态 |
| 整仓复制旧项目并去掉 DeerFlow | 迁移快 | 大量页面/路由/交易代码和 Python 依赖仍被打包，边界不清 | 不采用 |
| 抽取 finfreedom 核心和数据适配器，保持标准 MCP，DSH bundle 自动挂载 | 保留原契约并隔离旧 Agent；其他 MCP 客户端也可使用 | 需拆开 `app.main`、数据库与权限耦合，并处理 Python/Node 安装 | **目标方案** |
| 直接将全部能力改写为 Cordis `ctx.tools` | DSH 内集成直接 | 失去独立 finfreedom MCP，双平台复用变差；需要重新写多源适配 | 不作为唯一入口 |

## 目标方案

```text
DSH web / tui / headless profile
  └─ dsh-financial-freedom bundle patch
       ├─ 官方 dsh-mcp-client → 本包 finfreedom MCP server（stdio）
       └─ 本包 Skill 注册器 → 内置 finfreedom Skills

finfreedom MCP server
  └─ 业务服务与策略边界
       ├─ 资源目录和受限个人写入
       ├─ 确定性研究工具与证据构造
       ├─ 公共/授权数据适配器和本地缓存
       └─ finfreedom 业务库（默认 SQLite / 可选 MySQL 兼容连接）、文档、记忆、审计
```

MCP server 可以独立运行。DSH 只负责启动/连接并向 Agent 暴露工具，不能把 Agent 决策逻辑搬回 finfreedom。业务核心选 Python 作为首选迁移语言，以复用现有市场适配器和计算逻辑；插件包需提供可重复、无需手动复制旧源码的 Python 环境安装/检查步骤。若目标 DSH 安装策略禁用安装脚本，则必须提供显式 `setup` 命令及安装诊断，安装成功的定义包含 setup 成功，不能把“npm 包已加入 profile”当成功。实施前验证这一点。

### Docker 与数据库结论

- DSH 的 [storage 家族](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/README.md)为宿主插件提供 JSON/SQLite KV 与 schema 校验，适合少量配置、工作区状态和 sidecar；[domain 层](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/storage-domain/README.md)没有跨表事务或二级索引，不能直接替代 finfreedom 的行情/日线/文档检索数据库。
- 上游新版 [SQLite storage](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/storage-sqlite/README.md)仍是 JSON 文档逐键存储，并非通用关系 SQL 服务。本机 DSH `0.1.1-rc.2` 的安装目录含 `dsh-storage-json`/`dsh-storage-domain`，未见 `dsh-storage-sqlite`；不能以新版文档推定当前本机可用。
- DSH 管理 Agent 会话、profile、插件与不含密码的连接配置；业务数据由 finfreedom 自有数据库适配层存储，默认 SQLite，可连接自建或 Docker 启动的 MySQL 兼容服务。首版仍是单 owner，公共源采集、索引、备份和 schema 升级均由 finfreedom 负责。默认安装无需 MySQL 容器。
- 宿主机没有 Docker 时直接走 DSH CLI + finfreedom Python 包 + 本地 SQLite 文件；原项目 `mysql_db.py` 已有非容器 SQLite 回退，源项目相关 35 个测试在该路径通过，但新插件仍须完成全量契约与负载验证。[SQLite 官方适用场景](https://www.sqlite.org/whentouse.html)支持单机低并发写用途。
- DSH 官方安装路径以 npm/CLI 和 profile bundle 为核心；本插件提供自己的 Dockerfile/Compose 作为可选部署包装，镜像内固定 Node、Python、DSH、插件版本，并挂载 DSH home 与 finfreedom 数据卷。Compose 默认 SQLite，可选独立 DB 容器，也可使用外部服务；Docker 不改变 MCP、Skill 或权限契约。详见 [部署规格](deployment.md)。

## 身份与写权限决策

现有 MCP 靠 `FINFREEDOM_MCP_OWNER_ID` 环境变量绑定 owner，原本由已认证 Web 服务注入。直接把它放进通用 DSH profile 会丧失登录身份边界。因此新实现先提供 **本机单 owner 模式**：安装配置中的 owner 由本机可信设置固定，模型不可修改；默认只读。多用户共享 DSH 进程不开放个人数据，直至有 DSH 会话身份到 finfreedom owner 的可信映射和逐会话授权测试。写入工具要通过 DSH 权限钩子和 finfreedom 服务端双重校验；仅有自然语言“请写入”不能替代运行时授权记录。

## DSH Agent 与 AI 职责

- DSH 内部 Agent 接管旧 DeerFlow 的对话循环、工具选择、研究组织与回答生成。finfreedom 保留 MCP 数据访问、确定性计算、金融数据校验和业务写入边界；finfreedom 运行时不再配置或自行调用研究 LLM。
- 持仓截图通过 DSH 原生附件进入当前会话，由支持 image 的模型识别；Agent 把结果交给 `prepare_holdings_import`，finfreedom 负责字段校验、缺项/警告和待确认草稿。DSH 的模型目录按路由声明输入模态；使用不支持 image 的模型时要切换模型或改用文字输入。[附件能力说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/attachment/README.md)、[模型输入模态配置](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/user/guide/providers.md)。
- 这不代表所有旧 AI 页面流程都会随 Agent 替换而自动迁移。原有 AI 模拟盘任务会产生模拟委托；本期按既定信息查询范围只读保留账户/委托/任务查询，不开放 AI 创建模拟委托。

## 包装与兼容风险

- `dsh plugin --profile <name> add <source>` 是逐 profile 操作；“整个 DSH”需安装脚本遍历现有 profile，并输出每个 profile 的成功/失败。新增 profile 后重跑。不得把用户 home 补丁当成无需依赖解析的万能挂载点。
- Patch 中引用的 MCP server 路径须随 npm/link/Git 安装方式正确解析，禁止硬编码开发机绝对路径。
- 安装阶段不读取或复制 Financial Freedom 的 `.env`、数据库或私有 Skill；新实例生成独立私有配置。
- 原 `platform_mcp.research` 通过 `deerflow_worker._make_tools` 创建工具对象。抽取后必须改成独立工厂，并证明运行依赖图不含 DeerFlow。
- 原 `prepare_holdings_import` 生成旧网页 hash URL；在 DSH 必须改为草稿 ID + 可读摘要 + 明确的用户核对/提交协议。
- 旧 `write(holdings, replace_snapshot)` 源码表面调用没有在这一层检查 `expected_updated_at`；实施须追到 `holdings.save_snapshot` 的真实校验并以测试锁定行为。
- 旧 `documents`、`backtests`、部分缓存表是共享数据；新 schema 要明确 owner 范围，避免沿用旧共享可见性。
- 源 `financial-freedom/LICENSE` 为 PolyForm Noncommercial 1.0.0；若复制或发布其代码，须保留相应许可文本与 notices，并在发布前确认分发方式符合许可。第三方数据和依赖还需分别核对许可。

## 未决实现核验

1. 固定 DSH 目标版本并验证 bundle patch、MCP client、Skill 注入和 profile 安装行为；版本不兼容时记录兼容层，而非修改 DSH 核心。
2. 验证 finfreedom SQLite 的索引、WAL、备份和文档存储足以支撑默认查询/采集量；完成 MySQL 兼容适配器与相同业务契约，测试自建/容器服务、schema 升级、备份和切换。
3. 核对当前源项目各公共数据接口的实际可用性、许可及速率；失效接口需提供明确 `unavailable`，不能假装能力完整。
4. 验证 DSH 工具策略能否按单工具默认屏蔽 `write`；若做不到，拆为可选写入 bundle，主 bundle 只提供只读工具。
5. 验证目标 DSH 版本的插件配置页面、可信管理操作、`ctx.credentials` 与页面导航；若本机 `0.1.1-rc.2` 缺失必需接口，明确最低支持版本或提供等效安全宿主界面，不能以普通对话/命令直接接收密码。
