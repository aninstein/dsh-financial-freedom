# 实施计划

**状态：** 规格阶段。此文给出架构、顺序和验证门槛，不表示代码已实现。

## 交付结构（目标）

```text
package.json                 DSH bundle 声明、兼容版本、发布文件
cordis.patch.yml             挂载 finfreedom MCP 与 Skill 注册器
src/dsh/                     DSH 侧宿主插件和安装诊断
finfreedom/                       脱离 app.main/DeerFlow 的业务服务与 MCP server
finfreedom/providers/             公共行情、基金、新闻、流动性、板块、可选券商只读适配器
finfreedom/storage/               SQLite/MySQL 适配器、统一 schema 语义、升级与 owner 数据仓库
skills/<skill>/SKILL.md      随包金融研究 Skills
scripts/                     安装、预检、备份与回滚
tests/                       finfreedom 契约、持久化、DSH profile 集成测试
Dockerfile / compose.yaml     可选部署；默认单容器 SQLite，可加独立数据库服务
specs/                       本规格及后续变更
```

目录是目标，不要求先铺空文件。所有运行代码不得 import 旧仓库路径或 DeerFlow 模块。

## 建设顺序

### M0：冻结基线与技术探针

- 从源项目当前工作区导出 `catalog`、研究工具 schema、MCP tool list、Skill 列表及示例响应，记录源码 revision、未提交差异范围、数据 schema 版本。
- 在隔离 DSH profile 上做最小 bundle/MCP/Skill 探针，验证本机 `0.1.1-rc.2` 和目标发布版；确定 profile 安装、插件配置页面、凭据服务、管理身份和路径解析。
- 形成逐项实现矩阵，标注“纯计算 / 本地数据 / 公共源 / 可选授权源 / 原平台 UI 语义”及 P0 阻塞。

### M1：独立 finfreedom 核心与数据

- 把 `platform_mcp` 的目录、参数校验、owner 范围和写入边界移至新业务层；去除 `app.main` 与 `deerflow_worker` 依赖。
- 建立统一业务存储接口、SQLite/MySQL 兼容适配器、schema 升级、文件数据目录与分后端备份。实现默认 SQLite 首次自动建库、外部库预检和空数据状态。
- 移植确定性统计、回测、证据构造，保留源/采集/报告时间与单位。
- 分域实现 `capability-inventory.md` 的 36 个 read、25 个 research；每完成一域即做源项目对照测试。

### M2：DSH 和 MCP 封装

- 标准 MCP server 暴露五个顶层入口；DSH bundle 自动注册连接与 Skills。
- 安装工具处理现有 profile，逐 profile 验证配置层和实连工具；冲突或缺依赖时有清晰诊断。
- 添加只读默认策略、写权限开关与本机 owner 配置；写入走 finfreedom 服务端再验证。
- 实现 DSH 工作台 finfreedom 数据库设置页与安全凭据保存；对话中接受非秘密连接描述，生成草稿并引导到同一设置页。连接测试、启用、切回、状态、审计共用宿主侧管理服务。

### M3：扩展、部署与完整验证

- 随包 Skill 和 DSH 第三方 Skill/MCP 安装入口；凭据隔离和权限复核。
- 构建 Dockerfile/Compose，默认 SQLite、可选数据库容器或外部服务；验证空卷首次启动、容器重建后保留新数据、备份恢复和版本回滚。
- 将可选数据库容器模板接入 DSH 部署助手：用户提出时预检 Docker、幂等启动、保存私有凭据、健康检查，再生成同一数据库设置流程的连接草稿。
- 旧服务停机，运行安装/升级/卸载、故障恢复、数据源断线、跨 owner、路径注入与写入冲突场景。

## 关键设计边界

- **传输：** MCP 保持跨宿主接口；DSH 通过官方 client 接入，Skill 经 DSH 注册表按需加载。
- **源适配：** 每个数据源实现统一 `fetch → validate → normalize → cache`，保留原始源标识和失效原因；查询缓存与主动采集分开。
- **持久化：** finfreedom 自有业务库默认 SQLite，可切换 MySQL 兼容连接；DSH 保存 Agent 会话、profile 与不含密码的连接配置，密码存凭据层。个人状态与市场缓存分开，owner 相关表强制 owner 键；新安装从空库开始，写入按事务提交。切换连接不迁移数据。
- **安全：** MCP server 默认为仅本机 stdio；外部 HTTP 若后续需要，必须另设认证，不把 DSH 进程环境当远程身份凭据。
- **兼容：** 以契约兼容为优先，确需改变的旧 UI 字段/URL 使用版本化返回并在迁移说明中列出。

## 质量门槛

| 阶段 | 可继续条件 |
| --- | --- |
| M0 → M1 | DSH 探针在目标版本成功，插件配置页/凭据接口可用，能力清单与源 `catalog` 无遗漏 |
| M1 → M2 | 核心不依赖旧仓库/DeerFlow，资源与工具完成对照；SQLite/MySQL 兼容契约通过，无数据返回明确状态 |
| M2 → M3 | 每个目标 profile 可实际调用 finfreedom `catalog`，Skill 可发现，重复安装无冲突 |
| 完成 | 规格的全部验收场景通过；默认 SQLite、外部库连接与切换、空卷与重建验证通过；旧进程停机后仍可运行；能力矩阵没有虚假“可用” |

## 运行与发布产物

- npm/Git 可安装 bundle、可独立启动的 finfreedom MCP、锁定依赖、兼容矩阵和 checksum。
- `install`, `doctor`, `backup`, `uninstall` 命令、Dockerfile/Compose 及中文快速开始。
- 每次发布附能力差异、存储 schema 升级、破坏性变更与回滚说明。
