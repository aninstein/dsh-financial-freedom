# 规格评审与后续实施入口

当前仓库只有规格，不能执行 `dsh plugin add` 来获得 finfreedom 能力。

完成后的默认使用方式是宿主机直接安装 DSH 与 finfreedom 插件，连接本地 SQLite 文件。需要外部库时可在 DSH 工作台的 finfreedom 数据库设置中连接自建或 Docker 启动的 MySQL 兼容服务；DSH 对话可用不含密码的地址准备连接草稿。默认安装不要求 Docker 或 MySQL 服务；新安装从空库启动，不迁移旧数据。

预期对话示例：`帮我把 finfreedom 连接到 mysql://finfreedom_user@127.0.0.1:3306/finfreedom，数据库由我自己的 Docker 启动`。DSH 应解析主机、端口、库名和用户名，打开待确认的工作台配置；用户在安全表单中输入密码并执行「测试连接 → 启用」。若 DSH 也运行在 Compose 容器中，示例地址应改为数据库服务名与容器内端口。完整含密码的 URI 不应粘贴到普通对话。

## 评审顺序

1. 阅读 [功能规格](spec.md)，确认目标是独立 DSH 插件、保留 finfreedom MCP 与 Skills，以及默认不提供交易执行。
2. 阅读 [能力盘点](capability-inventory.md)，确认 36/25/5 的迁移边界及可选富途/长桥数据的定义。
3. 阅读 [方案调研](research.md) 与 [实施计划](plan.md)，确认先在隔离 profile 验证本机 DSH 版本、再抽取 finfreedom 核心。
4. 阅读 [数据模型](data-model.md)、[部署规格](deployment.md) 和 [接口契约](contracts.md)，确认单 owner 初始模式、写入门控、空库和持久卷方式。
5. 以 [任务清单](tasks.md) 启动实施；每项完成后更新能力矩阵和验证证据。

## 需要在实施前定版的选择

- 目标运行 profile 范围：现有 web/tui/headless 等全部 profile，或用户指定的一组；安装器可支持两种模式。
- finfreedom 业务数据默认使用自有 SQLite，可切换到 MySQL 兼容服务；DSH 的 KV/会话存储不替代关系型行情与文档查询。需在实施中验证两种后端的 schema、索引、写入量、备份和切换行为。
- 写工具启用方式：若 DSH 目标版本无法按工具默认关闭 `write`，将其拆成单独可选 bundle。
- 图片持仓草稿：由 DSH 会话的视觉模型读取附件，再让 finfreedom `prepare_holdings_import` 校验并生成待确认草稿；没有支持 image 的当前模型时提示切换或手动输入，不能声称已识别。

这些选择不阻塞基线盘点、DSH 探针和只读核心的实现，但阻塞最终“全部能力完成”的判定。旧用户数据明确不迁移。
