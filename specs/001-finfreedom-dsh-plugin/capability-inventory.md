# 原项目能力盘点与迁移矩阵

**盘点时间：** 2026-10-29
**基线：** 相邻 `financial-freedom` 工作区的 `app/platform_mcp.py`、`app/platform_mcp_server.py`、`app/ai_agent.py`、`app/ai_tools.py` 与 `app/agent_extensions.py`。源工作区有未提交修改；实施时须重新生成清单并审查差异。

**状态说明：** 本文所有条目为“需迁移”，不表示已在本仓库实现。`read` 宽查询只读本机缓存，按需采集主要通过 `research` 或专门适配器完成。

源项目当前的资源描述和 25 个公开研究工具参数已固定为 [机器可读契约快照](legacy-contract.json)，供后续逐项对照；该文件不是新插件的已实现能力目录。

## MCP 顶层工具（5）

| 工具 | 当前行为 | 迁移验收 |
| --- | --- | --- |
| `catalog` | 列出资源、研究工具、写动作与限制 | 完整、版本化、与实际可用能力一致 |
| `read` | 按命名资源读取 owner 范围内数据 | 36 个资源逐项等价，未知项拒绝 |
| `research` | 调用受限投研工具并返回证据 | 25 个公开工具逐项等价，缺参拒绝 |
| `prepare_holdings_import` | 接收 DSH Agent 从本轮文字或视觉模型读取图片后整理的持仓内容并生成草稿 | finfreedom 不调用 LLM；校验并只建草稿，缺项可机读，不自动保存 |
| `write` | 修改个人工作台内容 | 默认关闭，明确授权、乐观锁与审计 |

## `read` 资源（36）

| 域 | 资源 | 来源与关键参数 |
| --- | --- | --- |
| 工作台 | `cards`, `calendar` | owner 工作台状态与版本 |
| 个人资产 | `holdings` | owner 持仓；`currency` |
| 本地模拟 | `paper_local_accounts`, `paper_local_orders`, `paper_local_ai_runs` | owner 账户；`account_id`/`run_id`、分页 |
| 富途模拟 | `paper_futu_accounts`, `paper_futu_orders` | OpenD SIMULATE，只读；`connection_id`、分页 |
| 富途真实 | `live_futu_accounts`, `live_futu_orders` | OpenD REAL，只读；`connection_id`、分页 |
| 自选与行情 | `watchlist`, `quotes`, `market_status`, `market_calendar` | 本地缓存/日历；市场、查询、日期、分页 |
| 指数 | `indices`, `index`, `index_live` | 指数目录、日线分析、盘中/延迟快照；`index_id`、`limit` |
| 数据源 | `providers` | 提供方状态、覆盖和错误 |
| 市场研究 | `news`, `liquidity`, `sectors`, `flows` | 新闻、央行公开市场操作、轮动、资金；关键词/分页 |
| 标的研究 | `instrument`, `instrument_search`, `bars` | 个股分项、名称/代码搜索、日线；标的/日期/条数 |
| 文档 | `documents`, `document_page` | 已导入文档目录、页文本；`document_id`、`page` |
| 历史记录 | `research`, `backtests`, `calendar_insights` | owner 投研记录、回测、指定日期观察 |
| 记忆与运行 | `memory_settings`, `agent_status`, `extensions`, `wiki_tree`, `wiki_file`, `memory` | owner 记忆、运行状态、扩展元数据；路径/查询 |

实现时按这 36 个 **原始资源名** 建立一对一表；`agent_status` 应改为报告 DSH/finfreedom 运行状态，不再报告 DeerFlow。`extensions` 应报告 DSH 内实际挂载的 finfreedom/第三方扩展，不得假称旧平台设置页仍存在。新安装不会有旧富途委托；以后产生的委托记录也只能称为“本平台记录”，不能代表券商全部历史。

## `research` 工具（25 个公开；1 个原实现但未公开）

| 域 | 工具名 | 关键数据/动作 |
| --- | --- | --- |
| 记忆 | `get_investment_memory`, `get_memory_entry` | owner 归档记忆召回及单条查看 |
| 自选/市场 | `get_watchlist`, `get_market_news`, `get_macro_liquidity`, `get_sector_rotation` | 自选、新闻、央行逆回购、行业轮动 |
| 指数/周期/资金 | `get_historical_cycles`, `get_index_analysis`, `get_market_flow_history`, `get_flow_data_coverage` | 确定性统计、指数、资金与覆盖 |
| 标的/板块 | `get_stock_dossier`, `search_instruments`, `get_sector_overview`, `get_market_overview`, `get_instrument_research`, `get_stock_financials` | 资料、搜索、广度、财务 |
| 基金 | `collect_fund_disclosures`, `screen_funds`, `search_fund_directory`, `get_fund_research`, `get_fund_holdings`, `get_fund_trade_changes` | 定期披露、目录、净值、筛选、重大买卖 |
| 文档 | `search_uploaded_documents`, `read_uploaded_document` | 已导入材料检索、逐页片段 |
| 回测 | `run_sma_backtest` | 确定性 SMA 历史回测；不触发交易 |

`get_account_snapshot` 在旧 `ai_tools.py` 有实现，但 `platform_mcp.py` 的公开目录显式排除它。新插件保持未公开；账户只通过受信 owner 的 `read` 资源读取。若以后需要按本轮选择授权，单独评审契约。

## `write` 资源（5）与草稿

| 资源 | 动作 | 约束 |
| --- | --- | --- |
| `cards` | `set_layout`, `create_note`, `update_note`, `delete_note`, `set_builtin_note` | `expected_version`；只改布局和文字，不改行情 |
| `calendar` | `create`, `update`, `delete`, `acknowledge` | `expected_version`；`kind` 为 plan/event/subscription |
| `holdings` | `replace_snapshot` | owner、币种、快照版本与核对；绝不触发交易 |
| `watchlist` | `add`, `remove` | 标的格式与存在性校验 |
| `wiki_file` | `edit` | `expected_sha256`；路径隔离 |

`prepare_holdings_import` 是第六类 **工作流**，只保存待核对草稿。图片由 DSH 当前会话通过支持 image 的模型识别，finfreedom 工具接收 Agent 提取出的结构化/文字内容并做字段与金融数据校验；finfreedom 不再自行选择模型或发送图片给模型。原 `review_url` 指向旧网页；新实现必须提供 DSH 可用的审核状态和提交边界，不能继续返回无效 URL。

## 数据获取与扩展来源

- 公共市场适配：AKShare 背后的东方财富等网页源、腾讯日线回退、东方财富基金目录/净值/费率与持仓披露、央行公告、财经快讯、行业与资金统计。它们可能限流、变更字段或停止提供；返回源状态和缓存时点。
- 可选授权源：富途 OpenD 行情/账户只读，长桥行情；需要用户自己的连接与权限，不在仓库预置凭据。指数来源与个股代码需分别校验。
- 旧本地数据：MySQL 行情/日线/文档/回测/研究记录、owner 工作台与持仓、投资记忆 wiki、上传图片/文档。仅作为数据模型与行为参考，**不迁移旧数据**；新插件从空库开始采集与保存。
- Skill 当前存储目录 `data/agent-extensions/skills` 在本地为空；原系统具备 ZIP/GitHub Skill 安装、YAML 元数据、按需读取参考文件的能力。新插件提供随包 Skill 和 DSH 的后续安装入口，不导入旧私有目录。
- 第三方 MCP 当前支持 stdio 与 Streamable HTTP，默认只向投研暴露只读工具；新配置由用户在 DSH 侧建立，需复核连接命令、密钥与写权限。

## 逐项验收记录模板

每个条目在实现时新增记录：`原名 | 新入口 | 数据源 | owner 范围 | 参数 schema | 空数据行为 | 错误语义 | 来源/时点字段 | 契约测试 | 结果`。不得仅凭 `catalog` 中存在名称判定完成。
