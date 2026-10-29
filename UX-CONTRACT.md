# finfreedom in DSH: interface contract

finfreedom navigation opens a page beside the DSH sidebar. Returning to the chat or
selecting a DSH session restores the existing conversation without changing it.
The first three links are market overview, holdings and watchlist. A 工作台 entry opens the workspace; the workspace rail includes these high-frequency entries and all other tools, grouped under 常用, 市场 and 分析, with 数据与设置 at the bottom. 交易日历 and 投资记忆 remain in the content header. It shows the finfreedom mark and expands on hover or keyboard focus. Collapsing the DSH sidebar keeps accessible labels on its icon controls.

finfreedom pages use a shared read-only data adapter. Pending requests show a
loading state, failed requests show a retry, empty results are distinguished
from an unavailable data capability, and existing timestamps and sources are
retained. No sample financial values are shown. Table results are bounded by
the underlying MCP query; horizontal overflow belongs to the table itself.

Personal records remain bound to finfreedom's trusted local owner. This first UI
does not provide order placement or database credential entry. A database
settings form requires the DSH trusted settings and credentials integration
described in `specs/001-finfreedom-dsh-plugin/contracts.md`.

Visual tokens are owned by the DSH theme and mapped in [DESIGN.md](DESIGN.md).

The calendar defaults to real holdings, with CNY, HKD and USD selected separately. Daily price movement is an estimate from previously recorded quantities and consecutive exchange-session closing bars, excluding trades, fees and cash flow. Dates without prior holdings, complete bars, or with changed holdings are unavailable; no current position is backfilled into history. The original simulated-account option remains separate.

Workspace AI actions create a new ungrouped DSH session and populate its composer with the page's suggested prompt. The draft is editable and is not submitted automatically; the prior conversation and draft are preserved. In DSH 0.1.1-rc.2 a blank session without a workspace cannot be sent until the user selects a workspace.

The 功能引导 entry is available in both the DSH sidebar and the 常用 workspace rail. Each workflow shows its description, bundled skill names and expandable exact prompt; starting it opens a new DSH session with that prompt as an editable draft. Light and dark appearance follow the workspace theme.

AI投研 defaults to 推荐 and provides 收藏, 我的, and 内置词条 in a shared navigation above the selected view. Favoriting freezes the current Markdown; editing stores a personal version and updates its favorite snapshot when applicable. Plugin upgrades can change only unedited, unfavorited built-ins. Cards open DSH drafts, while separate controls edit or favorite. The UI and MCP share owner-scoped, version-checked storage.

AI投研词条按类别展示，内置词条自 added_at 起 30 天显示新标识并优先排列；收藏与个人修改的 Markdown 保留原值。所有内置词条引用的 Skill 必须随插件一起分发并注册。
