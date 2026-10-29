# Docker、插件安装与数据库方案

**状态：** 设计决定；尚未提供 Dockerfile/Compose 或可运行插件。

## DSH 已解决与 finfreedom 仍需解决的部分

| 问题 | DSH 提供 | 本项目决定 |
| --- | --- | --- |
| Agent 循环、模型、会话 | DSH profile 与会话持久化 | 直接使用 DSH，不再运行 DeerFlow |
| 插件安装 | `dsh plugin --profile <name> add`，bundle patch 自动加入 profile | 打包 finfreedom bundle，提供全部现有 profile 的幂等安装/doctor |
| MCP 接入 | 官方 `dsh-mcp-client` 可将 stdio/HTTP 工具注册为 `mcp__finfreedom__*` | 同包启动独立 finfreedom stdio MCP |
| Skill 加载 | DSH Skill 注册表和文件 provider | 随包注册 `finfreedom-*` Skills |
| 少量宿主状态 | `ctx.storage` 的 JSON/SQLite KV（取决于 DSH 版本） | 只用于轻量插件配置；本机 rc.2 不依赖新 SQLite 后端 |
| 行情/日线/文档/研究数据 | 无 finfreedom 业务 schema、采集器或关系查询服务 | finfreedom 业务库默认 SQLite，可连接 MySQL 兼容服务；文件目录独立，从空库开始 |
| 数据库设置与凭据 | 插件配置页面扩展点和 `ctx.credentials`（需锁定版本验证） | 工作台「插件 → finfreedom → 数据库」提供测试/切换；密码经安全表单写入凭据层 |
| Docker 镜像/Compose | DSH CLI 可在容器中运行；官方源码主要定义 npm/CLI 启动与 profile | 本仓库交付并维护 Dockerfile/Compose，不依赖第三方镜像 |

DSH [storage 包说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/README.md)和 [domain 限制](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/storage-domain/README.md)表明它是宿主 KV/JSON 文档存储；没有 finfreedom 需要的二级索引、跨表事务与多进程协调。新版 `dsh-storage-sqlite` 也只是 SQLite 上的逐键 JSON 文档层，不能等同通用业务 SQL 数据库。当前本机 `0.1.1-rc.2` 未打包该后端，因此首版不依赖它。

## 无 Docker 的本机安装（首选路径）

默认安装不要求宿主机安装 Docker、MySQL 服务或 SQLite 服务。SQLite 是随 Python 标准库访问的本地数据库文件；运行时仍需受支持的 Node/DSH、Python 和 finfreedom 包依赖。若用户选择外部 MySQL 兼容服务，只要求网络可达、账户权限和 TLS 配置满足预检，数据库可自建、托管或由另一台机器/本机 Docker 运行。

1. 固定 DSH 与插件版本，安装 `@deepseek-ai/dsh`。
2. 对目标 profile 执行 DSH 官方 `plugin add`；安装器遍历现有 profile，重复执行不生成重复挂载。
3. 安装器准备 finfreedom Python 运行环境和私有 `FINFREEDOM_DATA_DIR`，首次启动自动创建默认 SQLite schema；不读取旧 Financial Freedom 数据。默认路径由本机配置决定，doctor 输出绝对路径。
4. `doctor` 检查 bundle patch、finfreedom MCP 握手、五个工具、Skill 列表、数据目录权限和 schema 版本。成功后再宣告安装完成。

新 profile 需要重新运行安装器。卸载移除 profile 中的 bundle，保留新产生的数据目录；删除数据必须是独立显式操作。

原项目 `app/mysql_db.py` 在没有 MySQL 凭据且非容器时已使用 `sqlite3` 回退；本次在源工作区用该路径运行 `tests/test_platform_mcp.py`、`tests/test_holdings.py`、`tests/test_investment_memory.py`，**35 个测试通过**。这证明部分核心行为能在 SQLite 上运行，但不证明全部 36 个资源、25 个研究工具和长期采集负载都已等价。原 Docker 路径明确禁止 SQLite 回退；新插件必须实现正式的 SQLite 连接、锁、升级和备份，而不是仅改变 `CONTAINER_RUNTIME` 环境变量。

SQLite 可以覆盖首版单机单 owner 的关系查询和事务需求。它不是 MySQL 的无修改替代品：须拆分旧 MySQL 适配层中的 `GET_LOCK`、`information_schema`、DDL 转换与数据库方言，分别测试索引、并发写、长查询、FTS 与文件生命周期。SQLite 使用本机磁盘、WAL、`busy_timeout` 和有界写队列；MySQL 兼容适配器使用服务端事务、连接池和匹配的 schema 迁移。[SQLite 官方适用场景](https://www.sqlite.org/whentouse.html)说明本机低写并发适合 SQLite，而多并发写或跨机器共享更适合服务端数据库；[WAL 文档](https://www.sqlite.org/wal.html)说明可同时读写，但同一数据库仍只有一个 writer，且 WAL 不适用于网络文件系统。

## 工作台数据库连接配置

统一配置模型为“驱动 + 端点 + 凭据引用 + schema 状态”。工作台提供默认 SQLite 路径和 MySQL 兼容连接表单，包含主机、端口、库名、用户名、密码、TLS 模式、测试连接、启用和切回默认。页面只显示脱敏端点；密码存 DSH 凭据服务或经目标版本验证的等效私有存储。连接配置位于业务库外，切换数据库后仍可回到设置页。DSH 对话可根据不含密码的连接信息准备草稿并引导用户打开该页面；管理操作走同一校验器。本机 `0.1.1-rc.2` 对应「设置 → 插件 → 插件配置」的 `settings.plugin.item`，新版官方 [插件管理页面](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/client/ui-plugin-manager/README.md)对应 `plugins.bundle.config`；[凭据服务](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/credentials/README.md)与[命令日志语义](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/interaction/commands/README.md)是方案依据。页面注册、安全写入与跳转行为需在锁定版本运行验证。

`test` 限时检查连通性、认证、数据库权限、TLS 和 finfreedom schema；`apply` 在测试通过后原子切换。目标库为空时按受控流程初始化，已有非 finfreedom schema 或不兼容版本时拒绝覆盖。切换只改变后续读写所指数据库，不复制旧库数据；旧库和文件目录保留。外部数据库宕机时返回明确不可用，不静默回退 SQLite，以免读到另一份数据。

## Docker Compose 目标部署

```text
一个服务：dsh-finfreedom
  镜像：固定 Node 24 + DSH 版本 + Python 运行时 + finfreedom 插件/依赖
  进程：dsh web；finfreedom stdio MCP 由 DSH 插件启动
  卷一：DSH_HOME（profiles、会话、设置）
  卷二：FINFREEDOM_DATA_DIR（默认 SQLite/WAL、文档、wiki、审计）
  配置：模型密钥与可选数据源凭据由运行时 secret/env 注入，不写入镜像
  网络：Web 默认只绑定本机；远程访问需另行配置认证和反向代理
```

镜像构建阶段安装并锁定运行依赖；启动时只做幂等 profile 校验、当前连接检查和健康检查，不依赖运行时联网下载安装。默认 Compose 只运行 `dsh-finfreedom`，使用持久卷中的 SQLite 和 WAL；可选 Compose profile 增加 MySQL 兼容数据库容器，也可连接已有服务。DSH 在宿主机、DB 在 Docker 时使用映射到宿主机的端口；DSH 与 DB 同属 Compose 网络时使用数据库服务名，不能把容器内 `localhost` 当成另一个服务。多个 finfreedom 容器不得同时写同一 SQLite 卷。

若用户在 DSH 对话中要求“用 Docker 帮我启动数据库”，部署助手先检查 Docker 可用性，再按本仓库版本化 Compose 模板建立持久卷和数据库服务，等健康检查通过后生成不含密码的连接草稿并打开 finfreedom 数据库设置。生成的数据库密码通过 Docker secret/受限私有文件与工作台凭据层传递，不写入对话、命令行参数或 Compose 明文。重复执行不能重置已有库或覆盖凭据；Docker 不可用时引导使用 SQLite 或已有外部数据库。

## 部署验收

- 无 Docker 的本机安装和空卷 `compose up` 两条路径均可启动 DSH，finfreedom `catalog` 可调用；尚无行情/持仓时返回明确空数据状态。
- 工作台能测试并启用自建或 Docker 启动的 MySQL 兼容连接；DSH 对话可生成非秘密草稿；无密码泄露；切回 SQLite 后看到原 SQLite 数据，外部库数据仍在原库。
- 新采集一条行情、写入一项允许的个人状态、建立一条研究记录后，重建容器仍可查询。
- `docker compose down` 不删除卷；升级先备份 DSH home 与 finfreedom 数据，升级失败可用原镜像和备份恢复。
- 默认启动不要求数据库密码、旧 MySQL 连接或旧数据导入；选用外部库时凭据通过安全表单设置。
- 只读卷、数据目录权限错误、MCP 启动失败、schema 版本不兼容时健康检查失败并有可诊断错误；不能返回“插件正常”但工具不可用。
- 同一发布在 Linux amd64/arm64 的镜像构建与 MCP 启动通过；若平台不支持，发布说明明确标注。
- finfreedom SQLite 在线备份使用 [官方 backup API](https://www.sqlite.org/backup.html) 或等价一致性快照；不得在 WAL 正在写入时仅复制主 `.sqlite3` 文件作为可靠备份。
- 外部库备份使用其服务端一致性备份工具，并连同 finfreedom 文件目录验证恢复；仅备份 DSH home 不等于备份业务数据。

## 依据与版本差异

- DSH 官方 [CLI/profile 文档](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/reference/README.md)定义 profile、插件安装与启动。
- DSH 官方 [MCP client](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/mcp/mcp-client/README.md)定义工具挂载。
- DSH 官方 [存储包](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/README.md)、[SQLite backend](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/storage-sqlite/README.md)和 [domain 层](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/storage/storage-domain/README.md)定义 KV 适用范围与限制。
- 本机检查：`dsh --version` 为 `0.1.1-rc.2`；该安装目录有 `dsh-storage-json`、`dsh-storage-domain`，未发现 `dsh-storage-sqlite`。实施前仍需针对最终锁定版本复测。
