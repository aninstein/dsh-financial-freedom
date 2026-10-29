# 数据模型与持久化规格

新实例从空库开始，不导入旧 Financial Freedom 的 MySQL、数据卷、私有 Skill/MCP 配置或凭据。源项目数据模型仅用于定义行为与字段语义。

## 核心实体

| 实体 | 最小字段/约束 | 来源 |
| --- | --- | --- |
| `Owner` | `owner_id`、状态、创建时间；不由工具参数构造 | 可信本机配置或未来身份适配 |
| `Instrument` | `instrument_id=MARKET:SYMBOL`、名称、市场、资产类、交易币种、价格单位 | 行情目录 |
| `QuoteObservation` | 标的、价格、报价类型、交易所时间、接收时间、提供方、新鲜度、已知延迟 | 新采集行情 |
| `Bar` | 标的、周期、复权、OHLCV、源时间、接收时间、提供方、价格单位、数据版本 | 历史行情 |
| `ProviderState` | 来源、能力、覆盖、最近成功/尝试时间、错误、限流状态 | 适配器 |
| `MarketObservation` | 新闻/央行/板块/资金/指数的种类、原始 ID/URL、事件/披露/源时间、采集时间、原始与标准化值 | 公共/授权源 |
| `PortfolioSnapshot` | owner、币种、版本、持仓、资料市值/份额/成本、估值时点 | 新手工登记 |
| `AccountSnapshot` | owner、账户、模式 local/SIMULATE/REAL、连接、资产、估值完整性、时点 | 本地模拟/富途只读 |
| `Document` / `DocumentPage` | owner 或共享范围、文档 ID、SHA-256、类型、报告期、导入时间、页号、文本及原件路径 | 上传资料 |
| `ResearchRun` / `Evidence` | owner、运行 ID、问题、状态、工具参数、来源、时点、证据、结果、版本 | 新 DSH 工具运行 |
| `BacktestRun` | 策略、参数、标的、数据集版本、样本期、指标、运行时间 | 确定性回测 |
| `WorkspaceState` | owner、cards/calendar 状态、单调版本、修改时间 | 新建立状态 |
| `MemoryEntry` / `WikiFile` | owner、路径/ID、内容哈希、状态、来源锚点、保留期限 | 投资记忆 |
| `ImportDraft` | owner、草稿 ID、来源、识别结果、缺失项、状态、过期时间 | 持仓导入 |
| `SkillInstall` / `McpConnection` | 名称、来源、内容哈希/配置引用、权限状态、安装时间 | DSH 新安装扩展 |
| `AuditEvent` | owner、动作、资源、结果、时间、版本/哈希、脱敏参数摘要 | 新写操作 |
| `DatabaseConnectionProfile` | 驱动、SQLite 文件路径或服务端主机/端口/库名/用户名、TLS 模式、凭据引用、配置版本、最近测试时间与脱敏状态 | DSH/finfreedom 宿主配置；不存入当前业务库 |

实现可按性能拆表，但上述字段和关系不可丢失。数值金额保留币种与单位；UTC 存储时间并输出可解释时区。所有 owner 私有数据查询必须带 owner 条件。报价的 exchange time、receive time 和 freshness 是不同字段。

## 存储边界

1. **DSH 负责：** Agent 会话日志、profile、模型凭据和 DSH 自身的轻量插件状态。DSH `ctx.storage` 是可选宿主 KV 能力，不承载 finfreedom 的市场时间序列和关系查询。
2. **finfreedom 负责：** 业务存储抽象提供 SQLite 与 MySQL 兼容两种适配器，默认 SQLite 文件；外部数据库可以自建，也可以由 Docker 启动。两种适配器实现同一业务 schema 语义、事务、索引、有界分页和错误契约。上传原件与 wiki 文件仍在 finfreedom 独立文件目录；连接外部数据库不会自动移动这些文件。
3. **首次启动：** 未配置连接时在私有数据目录创建默认 SQLite、执行当前 schema、创建 owner 绑定；行情、文档、持仓和研究为空。显式配置外部库时只对目标库按受控迁移建立或升级 schema，不修改其他库。`catalog` 仍列能力，但对应资源返回明确 `empty`/`unconfigured`，不生成示例或旧数据。
4. **升级：** finfreedom schema 版本单调增加；升级前备份数据库与文件目录，升级失败不启动写入。版本不匹配时明确报错，不静默重建或丢弃文件。
5. **配置边界：** 当前连接配置保存在业务库外的 DSH/finfreedom 私有宿主配置中，密码只保存在 DSH 凭据服务或等效私有存储，配置仅持有凭据引用。切换目标库时先测试连通性、权限、schema 和兼容版本，再原子更新活动连接；失败保留原连接。切换不迁移、合并、删除旧库数据。
6. **Docker：** DSH home 和 finfreedom 文件目录映射持久卷；默认 SQLite 的 WAL 与主库在同一可靠本地文件系统。外部数据库由独立服务维护，不与 finfreedom 数据卷耦合。只读卷、空间不足、权限错误导致健康检查失败并给出诊断。
7. **备份：** SQLite 使用在线备份 API 或一致性快照；MySQL 兼容库使用匹配服务端版本的一致性逻辑备份，均须与文件目录一起保存并做恢复演练。卸载插件保留用户数据。
8. **多进程：** SQLite 模式每个 finfreedom 数据卷只允许一个写入实例。外部库并不自动意味着可运行 finfreedom 多副本；多副本与跨进程采集协调需单独设计和验收。

## 数据保留与删除

- 新会话、记忆、上传资料按新用户设置保留期限；删除文档须令相关引用明确失效，不把旧摘要当有效原文。
- API 凭据、数据库密码、MCP env 和 owner 绑定存私有配置，权限 `0600` 或等效安全存储，不写入普通导出、DSH 对话记录或 MCP 返回。
- 研究证据保留历史所见版本；新采集不原地篡改旧 evidence。
- 公开行情数据不得因插件安装自动发布或再分发；仅本地/授权范围使用。
