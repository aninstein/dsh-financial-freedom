# DSH 插件收录准备

## 简介

finfreedom 是面向中文用户的个人投资研究工作台，为 DeepSeek Harness 提供市场与持仓查询、研究词条、MCP 工具和随包 Skills。默认使用本地 SQLite，支持连接本机富途 OpenD；富途实盘页面只读。

English: finfreedom adds a Chinese-language investment research workspace, market and portfolio queries, MCP tools, and bundled skills to DeepSeek Harness. It uses local SQLite by default; its Futu real-account view is read-only.

## 安装与验证

- 包名：`@finfreedom/dsh-plugin`；根目录 `package.json` 声明 `dsh.bundle.patch` 和 Web 客户端入口。
- 本地源码：在仓库根目录运行 `pnpm install --ignore-scripts`，再运行 `dsh plugin --profile web add .`。
- 可分发包：`pnpm pack`，然后 `dsh plugin --profile web add <生成的 tgz 路径>`。
- GitHub：`dsh plugin --profile web add github:aninstein/dsh-financial-freedom`（需要远程公开仓库包含当前代码）。
- 已测试：DSH 0.1.1-rc.2 Web；Node.js 22、Python 3.11+。其他 DSH 版本及桌面环境尚未验证。
- 首次启动自动建立 Python 环境并下载依赖；需要可访问 Python 包源，可能需要数分钟和额外磁盘空间。无需 Docker。
- 卸载：`dsh plugin --profile web remove @finfreedom/dsh-plugin`。业务数据和 Python 环境保留在 `$DSH_HOME/finfreedom`。
- 建议核查：在全新 profile 安装并启动，访问工作台，确认 `mcp__finfreedom__catalog` 和内置 Skills 注册；卸载后检查用户数据仍保留。

## 公开发布前

1. 审核源码和第三方材料的分发权利；主项目采用 PolyForm Noncommercial 1.0.0，第三方 Skills 的许可见 [NOTICE.md](NOTICE.md)，与通常的开源许可证不同。收录方可能有额外许可要求。
2. 将代码推送到公开仓库，为 GitHub 仓库添加 `dsh-plugin` topic，检查 README 与默认分支可公开访问。
3. 如需 npm 市场安装，确认拥有 `@finfreedom` 命名空间的发布权限，检查包内容后发布；不要把未经发布的 npm 地址描述成已可安装。
4. 选择具体的精选目录或插件市场，按照其投稿规则提交；收录及精选与否取决于该目录的审核，不能由本仓库保证。
