# MCP、DSH 与权限契约

本文件定义目标外部行为。源项目的资源目录和 25 个公开研究工具参数已保存为 [机器可读契约快照](legacy-contract.json)，五个 MCP 顶层入口的输入 schema 见 [MCP 工具 Schema](mcp-tools.schema.json)。实现时须逐项对照，不能另写一份与运行时漂移的目录。资源专属 `params` 与写动作的 `data` 还需在对应实现中补全细化 schema，并纳入契约测试。

## MCP 入口

| 方法 | 输入 | 输出/错误 |
| --- | --- | --- |
| `catalog()` | 无 | `readable`, `writable`, `research_tools`, `workflow_tools`, actions, limits, `contract_version` |
| `read(resource, params?)` | 资源名 + 结构化筛选 | 数据 + 来源/时点/范围，或 404/422/403/503 等结构化错误 |
| `research(name, args?, session_id?)` | 公开研究工具名 + 参数 | 结果与 `evidence[]`；缺必填项 422；不可用源返回 data gap |
| `prepare_holdings_import(currency?, text?, positions?, session_id?)` | DSH Agent 从文字或会话图片中提取的内容；finfreedom MCP 不直接接收/转发原图 | 校验后的草稿 ID、识别项、缺失项、警告、`saved=false`；无可识别资料 422 |
| `write(resource, action, data)` | 受限资源 + 动作 + 乐观锁 | 新版本/结果与审计 ID；默认关闭，未授权 403，冲突 409 |

传输层的 MCP `isError` 与业务错误码要一致映射；不能把 Python 异常堆栈、密钥或 SQL 回给模型。单次结果超限时给出可继续分页的游标/参数。名称、原始资源名与研究工具名以 [能力盘点](capability-inventory.md) 为准。

## 统一返回信封

```json
{
  "contract_version": "1.x",
  "status": "ok | partial | unavailable",
  "data": {},
  "scope": { "owner_bound": true, "market": "CN", "coverage": "..." },
  "source": { "provider": "...", "source_id": "...", "url": null },
  "time": { "event_at": null, "published_at": null, "exchange_at": null, "received_at": null, "as_of": null },
  "unit": { "currency": null, "price_unit": null, "amount_unit": null },
  "freshness": "realtime | delayed | end_of_day | stale | unknown",
  "evidence": [],
  "data_gaps": [],
  "next": null
}
```

此信封是新版本目标；源项目 payload 仅供行为对照，差异由 `contract_version` 显式说明。`null` 是“未知/未提供”，不是零。事件时间、发布日期与接收时间不能合并。

## 权限矩阵

| 操作 | 默认 | 条件 |
| --- | --- | --- |
| 公共市场目录/缓存查询 | 允许 | 有界参数、源状态与新鲜度 |
| 主动公共源采集 | 允许 | 超时、速率、并发和结果上限 |
| owner 持仓/记忆/文档/账户读取 | 本机单 owner 模式允许 | 安装时可信绑定；多用户共享进程默认拒绝 |
| `write` | 拒绝 | 用户本轮明确要求 + DSH 门控 + finfreedom 服务端授权 + 版本校验 |
| 第三方 MCP 写工具 | 拒绝 | 逐连接审查和显式启用；不得继承旧配置的宽权限 |
| 模拟/真实交易执行 | 永久不暴露 | 无对应工具名和调用路径 |

## DSH 插件契约

- `package.json` 声明 `dsh.bundle.patch`，bundle patch 在 profile 中挂载 finfreedom MCP client 与 Skill 注册器。实际字段以固定的目标 DSH 版本验证。
- 对每个目标 profile，安装脚本输出：profile 名、包版本、patch 层、MCP 连接状态、实际工具名、Skill 名称、失败原因。
- 工具公共名期望为 `mcp__finfreedom__catalog/read/research/prepare_holdings_import/write`。若因 DSH 名称归一化发生变化，安装诊断报错并更新迁移说明，不静默接受。
- 随包 Skill 名称采用 `finfreedom-*` 命名空间；DSH Skill 注册表中的同名用户 Skill 冲突时优先用户覆盖，并显示来源。具体覆盖顺序通过目标版本实测锁定。

## 数据库管理契约（宿主侧，不进入 MCP 目录）

DSH 工作台的 finfreedom 数据库设置页显示当前驱动、脱敏端点、连接健康状态、schema 版本及最近测试时间。默认连接为 `sqlite`，可切换至 `mysql`；MariaDB 仅在完成兼容测试后列为受支持的 MySQL 兼容服务。服务端连接可由自建实例或 Docker 容器提供，配置流程相同。

| 操作 | 输入 | 结果与边界 |
| --- | --- | --- |
| `status` | 无 | 返回驱动、脱敏端点、连接和 schema 状态；不返回密码/完整 DSN |
| `prepare` | `sqlite` 文件路径，或 `mysql` 主机/端口/库名/用户名/TLS；不得含密码 | 生成一次性待确认草稿；对话助手可调用但不能启用连接 |
| `test` | 草稿 + 安全表单录入的凭据 | 限时连接、驱动/权限/schema 预检；不修改活动连接，不回显密钥 |
| `apply` | 已测试草稿的版本与可信用户操作 | 再检查目标及版本，原子切换活动连接；失败保留原连接；提示不复制数据 |
| `reset` | 可信用户操作 | 切回默认 SQLite 路径；原外部库不删除 |

普通 DSH 对话可接收**不含密码**的地址或部署描述，并调用 `prepare` 生成工作台安全表单的跳转/操作指引。含密码的完整 DSN 不作为普通对话或模型工具输入。密码只能经安全表单写入 DSH `ctx.credentials` 或经目标版本验证的等效私有凭据层；profile 仅持有凭据引用。DSH slash command 文档说明命令运行会写入 session log，因此不得把含密码的 DSN 直接作为命令参数。所有管理接口要求宿主可信身份，不从 MCP 的 `owner_id`、自然语言意图或工具参数推断授权。目标 DSH 版本若无法提供安全表单、凭据存储或可信管理身份，外部数据库启用能力不得标为完成。

连接解析只接受 `sqlite` 与 `mysql`，拒绝任意 URL scheme、内嵌 SQL、连接参数注入和未经允许的文件路径；服务端端点受部署方网络策略约束，连接与健康检查有超时。切换后查询与采集使用当前活动连接，处理中请求按切换版本完成或返回可重试错误，不能混写两个库。配置写入、测试结果与切换结果只记录脱敏审计信息。

## 必测反例

- 模型传 `owner_id`、任意 SQL/URL、未知资源、超长查询、负分页或超范围日期 → 拒绝。
- 同一 DSH 进程两位 owner 使用同一 MCP child → 私有数据拒绝，直到可信逐会话绑定实现。
- 旧缓存源断开 → 标 `stale/unavailable`，不输出“实时”。
- wiki 越界路径/会话摘要路径、Skill ZIP 越界/链接、第三方 MCP 回显密钥 → 拒绝或脱敏。
- 并发写同一 cards/calendar/wiki/holdings 版本 → 一方成功、一方 409；不丢更新。
- `research(get_account_snapshot)` 与任何交易订单调用 → 工具不存在/拒绝。
- 含密码 DSN 进入普通对话/斜杠命令、模型请求或日志 → 不得作为成功配置路径；安全表单输入在会话、日志、MCP 结果和导出中均不可见。
- 目标库连接失败、schema 不兼容、权限不足、切换中请求并发或 Docker DB 未就绪 → 原连接继续可用，诊断脱敏且可重试。
