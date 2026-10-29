# finfreedom

finfreedom 是面向国内用户的个人金融研究工作台，产品名称及相关商标归利长安（[lichangan.com](https://lichangan.com)）所有。

本仓库用于把原 Financial Freedom 项目的查询与投研能力重建为可安装的 DeepSeek Harness（DSH）插件。当前已开始实现，首个迁移切片包括 DSH stdio MCP bundle、默认 SQLite/可配置 MySQL 连接、owner 持仓读取与待核对导入草稿；写操作默认关闭。其余行情、研究与工作台资源仍在迁移中。旧用户数据不迁移；新安装从空数据目录开始采集和存储。

finfreedom 业务库默认 SQLite。目标插件会在 DSH 工作台提供数据库连接设置，可连接自建或 Docker 启动的 MySQL 兼容服务；DSH 对话可协助准备不含密码的连接草稿，密码经安全设置页保存。切换连接不自动迁移数据。

## 当前进度

- 本机 DSH `0.1.1-rc.2`：运行 `python3 -m finfreedom.cli install --profile web` 会在 `$DSH_HOME/finfreedom/venv` 创建独立 Python 3.11+ 环境、安装 MCP 依赖，并把 bundle 和随包 Skills 安装到 DSH。也可用 `--profile` 重复指定其他 profile。 插件自身也向 DSH 注册随包的 `install-futu-opend`、`futuapi` 和 `finfreedom-research` Skills；工作台「数据与设置」可将 OpenD 安装请求直接交给当前 DSH 对话。用户或项目中同名 Skill 仍优先生效。
- 安装入口使用上述命令：仅执行 `dsh plugin add` 不会创建 Python 虚拟环境或安装 Python MCP 依赖。源码以本地链接方式安装时，还需先在本仓库运行 `pnpm install --ignore-scripts` 安装插件的 Node 依赖。
- DSH 工具：`mcp__finfreedom__catalog/read/research/prepare_holdings_import/write` 已建立接口。当前可读持仓、自选、行情缓存、标的搜索、历史日线、用户文档/页、研究记录和回测记录；研究调用支持 `get_watchlist`、`search_instruments`、`get_historical_cycles`。未迁移项会在 `catalog.implementation_status` 中明确列出。持仓写入口仍受 `FINFREEDOM_ENABLE_WRITES` 管理员开关控制，默认关闭。
- 本机历史日线表与研究缓存 schema 已建好，但行情/基金/新闻采集器尚未迁移，因此新装实例的这些查询可能返回明确的空缓存状态。
- DSH Web 客户端扩展提供 finfreedom 侧栏导航和只读工作台页面；持仓、行情缓存、文档与历史记录读取已有入口，其余页面明确显示未接入。侧栏适配针对 DSH 0.1.1-rc.2，版本升级后需重新核对该版本的侧栏插槽。
- 持仓截图：DSH 视觉模型读取当前会话附件，finfreedom 只校验模型传来的结构化字段并保存草稿；finfreedom 不自行调用模型。
- 数据库：默认 SQLite；使用 `~/.dsh/finfreedom/venv/bin/finfreedom db configure-mysql --host <host> --database <name> --user <user>` 可隐藏输入 MySQL 密码，`~/.dsh/finfreedom/venv/bin/finfreedom db use-sqlite` 切回 SQLite。设置了 `DSH_HOME` 时将上述路径替换为对应目录。

该阶段尚未完成原项目各页面的完整业务流程、其余只读资源、22 个研究工具、全部受限写操作、工作台数据库设置 UI、Docker 部署与全量数据采集/数据库验收。

## 规格入口

- [项目章程](.specify/memory/constitution.md)
- [功能规格与验收](specs/001-finfreedom-dsh-plugin/spec.md)
- [现有能力盘点](specs/001-finfreedom-dsh-plugin/capability-inventory.md)
- [DSH 方案调研与技术决策](specs/001-finfreedom-dsh-plugin/research.md)
- [实施计划](specs/001-finfreedom-dsh-plugin/plan.md)
- [数据模型与持久化](specs/001-finfreedom-dsh-plugin/data-model.md)
- [Docker 与安装部署](specs/001-finfreedom-dsh-plugin/deployment.md)
- [MCP 与插件契约](specs/001-finfreedom-dsh-plugin/contracts.md)
- [源项目机器可读契约快照](specs/001-finfreedom-dsh-plugin/legacy-contract.json)
- [MCP 工具输入 Schema](specs/001-finfreedom-dsh-plugin/mcp-tools.schema.json)
- [任务清单](specs/001-finfreedom-dsh-plugin/tasks.md)
- [规格评审入口](specs/001-finfreedom-dsh-plugin/quickstart.md)

规格基线来自相邻的 `financial-freedom` 工作区，2026-10-29 读取时 HEAD 为 `0990e2808b8f547a17889e9b0385019f311a8ba5`，工作区另有未提交修改。实施前须重新冻结能力清单，不能假定该提交已包含全部当前行为。

## AI投研词条与内置 Skills

「AI投研」默认展示收藏，提供“我的”和“全部词条”，各视图按词条类别展示；内置新词条上线后 30 天内显示“新”并排在前面；点击词条会将其 Markdown 放进新的 DSH 对话草稿。支持收藏、新建及 Markdown 编辑；收藏保存快照，编辑过的词条归入“我的”，插件升级不会覆盖它们。通过 MCP `list_guide_entries` 和 `manage_guide_entry` 可在 DSH 中管理同一份词条，写入前须读取版本。DSH 当前版本要求新会话先选择工作区才能发送。

插件随包注册 `finfreedom-research`、`futuapi`、`install-futu-opend`，以及 Anthropic `financial-services` 的 `sector-overview`、`thesis-tracker`、`earnings-preview`、`morning-note`，以及组合风险、财务分析、基金分析和策略研究四个 finfreedom 专项 Skill；来源和许可证见 [NOTICE.md](NOTICE.md)。这些 Skill 提供研究方法，不包含额外数据订阅；研究数据取决于已接入的数据源。

另外内置 Anthropic 的 `earnings-analysis`、`catalyst-calendar`、`idea-generation`，以及 InvestSkill 适配的 `investskill-bear-case`、`investskill-fact-check`、`investskill-financial-report-analyst`。原始许可证、固定来源版本及适配说明见 NOTICE；上游的可选脚本与外部数据订阅不随包提供。

AI 投研页面的「新闻推荐」由 DSH 后台 Agent 使用 DSH 默认模型分析近期可获取的财经新闻，正常情况下每小时更新 4–6 个研究方向；也可手动更新。每条推荐保留新闻来源和发布时间，点击可带提示词进入对话，编辑保存后成为个人词条。更新失败时保留上次结果并显示状态；DSH 未运行时任务不会执行，重启后会继续检查。新闻与推荐仅供进一步研究，应核实原始来源。
