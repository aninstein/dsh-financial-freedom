# finfreedom · DeepSeek Harness 投研工作台

finfreedom 是一个 DeepSeek Harness（DSH）插件，提供中文投资研究工作台、市场与持仓数据查询、MCP 工具和投研 Skills。工作台使用 DSH 的会话和模型，默认将个人数据保存在本机 SQLite。产品名称及相关商标归利长安（[lichangan.com](https://lichangan.com)）所有。

## 功能

- 市场总览、指数、财经新闻、央行流动性、资金与板块数据；支持连接本机富途 OpenD，公开数据可能存在延迟或不可用。
- 持仓、自选、投资记忆、日历、策略研究及本地模拟交易。富途实盘页面目前只读，不支持发送真实订单。
- AI 投研词条支持分类、搜索、收藏与 Markdown 编辑；点击后将提示词带入 DSH 新对话。新闻推荐在 DSH 运行时由后台 Agent 定期生成。
- 随插件注册 finfreedom MCP 和 17 个 Skills；第三方来源及许可证见 [NOTICE.md](NOTICE.md)。模型能力、行情权限及数据时效由实际配置决定。

## 安装

**兼容性：已在 DSH 0.1.1-rc.2 的 Web profile 验证。** 其他版本或桌面环境尚未验证。需要 Node.js 22.19+、Python 3.11+、可访问 Python 包源的网络；无需 Docker。若系统有多个 Python，可用环境变量 `FINFREEDOM_PYTHON` 指向 Python 3.11+。

在项目目录中安装本地源码：

```sh
pnpm install --ignore-scripts
dsh plugin --profile web add .
dsh --profile web
```

插件首次启动时自动在 `$DSH_HOME/finfreedom`（默认 `~/.dsh/finfreedom`）准备独立 Python 环境并安装依赖；首次启动可能需要数分钟。失败时检查 Python 版本、网络及 DSH 日志后重启。插件更新时会准备对应版本的环境。Node、Python 环境及下载依赖需要一定磁盘空间。若从 npm 发布包安装，可用 `dsh plugin --profile web add @finfreedom/dsh-plugin`；从公开 GitHub 仓库安装可用 `dsh plugin --profile web add github:aninstein/dsh-financial-freedom`。发布前不要假定这两个远程来源已经可用。

打开 DSH 后选择侧栏的「AI投研」或「工作台」。富途行情需要自行启动并登录官方 OpenD；设置页可将安装请求交给 DSH。DSH 对话的图片识别依赖所选模型或视觉插件。默认不迁移旧项目数据；如需导入旧数据，请先备份并阅读 `finfreedom import-legacy --help`。

## 数据与卸载

数据默认位于 `$DSH_HOME/finfreedom`，包括数据库、推荐缓存和 Python 环境。当前提供命令行连接 MySQL 的能力：

```sh
~/.dsh/finfreedom/venv/bin/finfreedom db configure-mysql --host <host> --database <database> --user <user>
```

该命令需要事先用 `python3 -m finfreedom.cli install --profile web` 创建旧版 `venv`；密码在终端隐藏输入。默认自动安装生成的运行环境也可通过该环境的 Python 执行 `-m finfreedom.cli db ...`。数据库切换不会自动迁移数据。工作台中的数据库连接设置仍未完成。

移除插件：`dsh plugin --profile web remove @finfreedom/dsh-plugin`。用户数据及 Python 环境不会随插件自动删除，确认不再需要后可手动清理 `$DSH_HOME/finfreedom`。

## 开发与测试

```sh
pnpm install --ignore-scripts
node --test tests/*.test.mjs
python -m unittest discover -s tests -p 'test_*.py'
pnpm pack
```

Python 测试需要先安装 `pyproject.toml` 中的依赖。项目规格见 [specs/001-finfreedom-dsh-plugin](specs/001-finfreedom-dsh-plugin/spec.md)。

## 许可证

本项目包含原 Financial Freedom 项目代码，按 [PolyForm Noncommercial 1.0.0](LICENSE) 分发，仅允许该许可证所定义的非商业用途。第三方 Skills 分别按其所附许可证分发，详见 [NOTICE.md](NOTICE.md)。请在使用或再分发前核对适用条款。
