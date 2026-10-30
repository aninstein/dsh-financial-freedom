# DSH 插件收录准备

## 简介

finfreedom 是面向中文用户的个人投资研究工作台，为 DeepSeek Harness 提供市场与持仓查询、研究词条、MCP 工具和随包 Skills。默认使用本地 SQLite，支持连接本机富途 OpenD；富途实盘页面只读。

English: finfreedom adds a Chinese-language investment research workspace, market and portfolio queries, MCP tools, and bundled skills to DeepSeek Harness. It uses local SQLite by default; its Futu real-account view is read-only.

## 安装与验证

- 包名：`@finfreedom/dsh-plugin`；根目录 `package.json` 声明 `dsh.bundle.patch` 和 Web 客户端入口。
- 版本矩阵：插件 `0.1.x` 对应 DSH `0.1.1-rc.2`；插件 `0.2.x` 对应 DSH `0.2.1-rc.3`。新版本使用 DSH 0.2 会话控制器和工作区 API，MCP/Skills runtime peers 也要求 0.2.1，因此不兼容旧运行时。
- 本地源码：在仓库根目录运行 `pnpm install --ignore-scripts`，再运行 `dsh plugin --profile desktop add .`。
- 可分发包：`pnpm pack`，然后 `dsh plugin --profile desktop add <生成的 tgz 路径>`。
- GitHub：发布 `v0.2.0` 后可运行 `dsh plugin --profile desktop add github:aninstein/dsh-financial-freedom#v0.2.0`。
- 已核对：DSH `0.2.1-rc.3` 桌面 `app.asar` 中客户端模块、会话/工作区服务与 MCP/Skills peer 版本；隔离 CLI E2E 尚未通过，原因是 npm 上游未发布 `@deepseek-ai/dsh-tool-bash-persistent@0.2.1-rc.3`。Node.js 22、Python 3.11+。
- 首次启动自动建立 Python 环境并下载依赖；需要可访问 Python 包源，可能需要数分钟和额外磁盘空间。无需 Docker。
- 卸载：`dsh plugin --profile web remove @finfreedom/dsh-plugin`。业务数据和 Python 环境保留在 `$DSH_HOME/finfreedom`。
- 0.2.1 适配变更：客户端不再依赖已删除的 `dsh-client-runtime`，改用当前存在的 renderer/layout/conversation/workspace modules。新建对话时兼容 session create 返回值，先 retain session、等待 scope 可用、写入可编辑草稿，再由 `uiWorkspace.openSession` 打开；0.2.x manifest 限定 DSH 0.2.1，以避免旧运行时静默跳过或缺少新版本 peer API。
- 验收待完成：用可正常安装的 `@deepseek-ai/dsh@0.2.1-rc.3` 在全新隔离 profile 启动，访问工作台，确认客户端入口、MCP 工具和 17 个 Skills 注册。当前 npm 依赖问题修复后再进行完整 UI 验收。

## 公开发布前

1. 审核源码和第三方材料的分发权利；主项目采用 PolyForm Noncommercial 1.0.0，第三方 Skills 的许可见 [NOTICE.md](NOTICE.md)，与通常的开源许可证不同。收录方可能有额外许可要求。
2. 将代码推送到公开仓库，为 GitHub 仓库添加 `dsh-plugin` topic，检查 README 与默认分支可公开访问。
3. 如需 npm 市场安装，确认拥有 `@finfreedom` 命名空间的发布权限，检查包内容后发布；不要把未经发布的 npm 地址描述成已可安装。
4. 选择具体的精选目录或插件市场，按照其投稿规则提交；收录及精选与否取决于该目录的审核，不能由本仓库保证。
