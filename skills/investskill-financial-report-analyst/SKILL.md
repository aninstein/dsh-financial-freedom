---
name: investskill-financial-report-analyst
description: Analyze company financial reports (10-K, 10-Q, annual reports) and extract actionable investment insights — statement quality, red flags, and a signal. For a structured section-by-section summary document of a 10-K rather than an investment call, use 10k-digest
---


> finfreedom 适配：使用 DSH 和 finfreedom 可用的数据与文档工具；本 Skill 不包含上游可选脚本，也不保证实时行情、联网、SEC 数据或外部数据服务可用。缺少来源时明确说明，禁止虚构；按用户语言回复，仅输出研究内容，不自动交易或改写用户数据。

# Financial Report Analyst

## ⚠️ Data Verification — Do This Before Any Analysis

Before running any analysis, always retrieve the latest market data for the ticker:

1. **Fetch current price** — use web search or ask the user for the live price, 52-week range, and market cap. Never assume a price from training data.
2. **Confirm key figures** — the filing itself (form, fiscal period, filing date, accession number) and its headline figures — revenue, operating income, net income, OCF, capex, cash, debt, diluted shares — read from the statements, not a data site.
3. **State your data source** — fill in the `Data & Sources` header (next section) so the origin, as-of date, retrieval path, and confidence of every figure are explicit at the top of the output.
4. **Flag stale data explicitly** — if live data is unavailable, display this warning before proceeding:

> ⚠️ **Live data unavailable.** The following analysis uses training-data estimates which may be significantly out of date. Verify all prices and metrics before making any decisions.

Never silently substitute training-data estimates for current prices. When in doubt, ask the user to paste the latest quote.

---

## 📋 Data & Sources Header — Open Every Output With It

The first thing in the output is this provenance block, filled in — never left as placeholders. It is the standard documented on the [Data & Accuracy](https://yennanliu.github.io/InvestSkill/data-and-accuracy.html) page and the first thing `result-validator` looks for:

```
Data & Sources
  As of:      <date the figures represent, e.g. 2026-06-30>
  Source:     <primary docs — SEC EDGAR 10-K/10-Q, company IR, FRED, exchange data …>
  Retrieval:  <pasted by user | web/tool retrieval | model memory>
  Confidence: <HIGH | MEDIUM | LOW>
```

- `Retrieval: model memory` must be paired with `Confidence: LOW` — memory is a placeholder until confirmed against a primary source.
- Mixed sources: list each with its own as-of date rather than blending them.
- Sources disagree on the same figure (a closing price, a deal term): prefer the primary source (SEC filing, company release, exchange data) over an aggregator, then the most recent dated one. Show both values with their sources and dates, say which you used and why, and never average them.
- Data the user pasted is reported as `pasted by user`; do not upgrade its confidence beyond what the user's own source supports.

---

## 🌐 Output Language — `--lang zh-TW`

English is the default. With `--lang zh-TW` — or when the user writes in Traditional Chinese and asks for a Chinese answer — write the whole analysis in Traditional Chinese (繁體中文, Taiwan usage), keeping it machine-checkable:

- **Translate** every heading, narrative paragraph, table header and bullet. Give each metric's English name in brackets the first time it appears — 自由現金流（Free Cash Flow, FCF） — so the reader can match it to the glossary and to English analyses.
- **Keep in English** tickers, figures and units, SEC form and item names (10-K Item 7, Form 4), the four `Data & Sources` field labels (`As of`, `Source`, `Retrieval`, `Confidence` — the Retrieval value may be written in Chinese, e.g. 使用者提供), and the Investment Signal box and JSON footer exactly as specified — field names and the BULLISH / NEUTRAL / BEARISH, HIGH / MEDIUM / LOW, BUY / HOLD / SELL, STRONG / MODERATE / WEAK values. Tools parse them.
- Title the invalidation section **論點失效條件（Thesis Invalidation）**, and close with the disclaimer in Chinese: **免責聲明：** 僅供教育用途，非投資建議。
- Use Taiwan financial terms: 殖利率、本益比、營業利益率、自由現金流、聯準會、選擇權、買權／賣權、除息日、預扣稅.

---

Extract deep investment insights from official company financial filings and reports — 10-K annual reports, 10-Q quarterly reports, earnings press releases, proxy statements (DEF 14A), and investor presentations. Combines quantitative financial analysis with qualitative assessment of management tone, strategy, and risk disclosure.

## Overview

Official filings are the primary source of truth for company analysis. Unlike financial data terminals (which aggregate selected metrics), the actual 10-K and 10-Q contain management's own words, full footnote disclosures, legal risk factors, and accounting policy choices that are invisible in summary data feeds. This skill teaches you to read between the lines of official documents and convert dense regulatory language into actionable investment insights.

---

## How to Use

Provide the report in one of these ways:

```
# Paste report text directly
/financial-report-analyst [paste 10-K or 10-Q sections]

# Reference a specific ticker for the most recent filing
/financial-report-analyst AAPL 10-K

# Analyze a specific section
/financial-report-analyst MSFT 10-Q --section risk-factors

# Full deep-dive analysis
/financial-report-analyst NVDA 10-K --full

# Comparative: compare current vs prior period filing
/financial-report-analyst GOOGL --compare-prior
```

### Retrieving the filing — the keyless EDGAR path

When the user names a ticker instead of pasting text, this skill still fetches nothing by itself. If the host can fetch URLs, get the primary document from SEC EDGAR (free, no API key) and mark `Retrieval: web/tool retrieval`:

1. **Ticker → CIK:** `https://www.sec.gov/files/company_tickers.json` — match `ticker` (`BRK-B` for `BRK.B`), zero-pad `cik_str` to 10 digits.
2. **Filings index:** `https://data.sec.gov/submissions/CIK##########.json` — in `filings.recent`, the arrays `form` · `filingDate` · `reportDate` · `accessionNumber` · `primaryDocument` line up by index. Pick the newest row whose `form` is the one asked for: `10-K` (annual; `20-F` for foreign private issuers), `10-Q` (quarterly; `6-K` for foreign issuers), `8-K` (earnings release is usually Exhibit 99.1 in the filing folder), `DEF 14A` (proxy).
3. **Document:** `https://www.sec.gov/Archives/edgar/data/<CIK without leading zeros>/<accessionNumber without dashes>/<primaryDocument>` — the full filing as HTML. The folder's `<accessionNumber>-index.htm` lists every exhibit.
4. **Statement facts (to cross-check Item 8):** `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`.

Identify yourself with a `User-Agent` header (`Name email`) and stay under 10 requests per second. For `--compare-prior`, take the second-newest row of the same form. Cite accession number and filing date in the `Data & Sources` header.

If the host cannot fetch, ask the user to paste the sections — or, from the InvestSkill repository, to run `node scripts/fetch-edgar.js <TICKER> --form 10-Q` (saves the filing as text plus a `.json` with the header fields) or `node scripts/fetch-fundamentals.js <TICKER>` (a reconciled statement pack from the XBRL facts) — and mark `Retrieval: pasted by user`. With neither, proceed only under the ⚠️ warning above with `Confidence: LOW`.

---

## Sector KPI Packs (`--sector`)

Generic operating-company metrics mislead in five sectors. When the user passes `--sector <bank|insurer|reit|biotech|saas>` — or the company is clearly in one of them (SIC code, business description) — **swap the generic metrics for the sector pack, say which pack was applied, and drop the metrics in its "Ignore" line** (or show them only with a note that they are not meaningful here). Pull the KPIs from the 10-K / 10-Q and, where they are not GAAP line items (CET1, occupancy, NRR), from the company's supplemental disclosures, regulatory filings or earnings release — never from memory.

```
/stock-eval ZEPH --sector saas
/financial-report-analyst ZEPH 10-K --sector reit
```

**bank**
- *Swap in:* CET1 ratio vs. its regulatory minimum + buffers · net interest margin (NIM) · efficiency ratio (non-interest expense / revenue) · NPL ratio and net charge-off (NCO) ratio · allowance / loans · loan-to-deposit ratio · deposit beta (Δ deposit cost / Δ policy rate) and uninsured-deposit share · AOCI and held-to-maturity unrealised losses vs. tangible equity · ROTCE · P/TBV
- *Ignore:* P/E as the primary multiple, EV/EBITDA, Altman Z, Beneish, current ratio, DSO/DIO, debt/equity and FCF (deposits and loans are the business, not its financing)
- *Read:* efficiency < 60% is good; NCO ratio against the bank's own cycle history; HTM losses above ~25% of tangible equity are a warning; justify P/TBV with ROTCE (fair P/TBV ≈ ROTCE / cost of equity)

**insurer**
- *Swap in:* combined ratio = loss ratio + expense ratio (P&C) · prior-year reserve development (favourable / adverse, % of opening reserves) · net investment yield and portfolio credit mix · book value per share growth (with and ex-AOCI) · ROE · P/B · solvency: RBC ratio (US) or Solvency II ratio
- *Ignore:* EV/EBITDA, Altman Z, Beneish, FCF, working-capital days, and premium growth as a quality signal (fast growth can mean under-pricing)
- *Read:* combined ratio < 100% = underwriting profit; repeated adverse development is a major flag; BVPS growth plus dividends is the compounding measure; justify P/B with sustainable ROE

**reit**
- *Swap in:* FFO and AFFO per share (NAREIT FFO; AFFO deducts recurring capex, straight-line rent and leasing costs) · P/FFO and P/AFFO · occupancy · same-store NOI growth · weighted average lease expiry (WALE) and the lease-expiry ladder · net debt / EBITDA and fixed-charge coverage · AFFO payout ratio · NAV and implied cap rate
- *Ignore:* EPS and P/E (real-estate depreciation distorts GAAP earnings), Altman X2 (REITs must distribute income), FCF before AFFO adjustments
- *Read:* AFFO payout < ~85% leaves room to grow the dividend, > 100% is unfunded; sector net debt / EBITDA typically runs 5–7×; falling occupancy or negative same-store NOI is the operating warning

**biotech**
- *Swap in:* cash runway in quarters = (cash + investments) / quarterly operating burn · pipeline table (asset, indication, phase, next readout, partner, economics) · probability of success to approval by phase · catalysts (readouts, PDUFA dates, advisory committees) · partnerships (upfronts, milestones, royalties, who holds which rights) · dilution history (shares outstanding over 3–5 years, ATM use, offerings and their discounts)
- *Ignore:* P/E, EV/EBITDA, margins, ROIC, Piotroski F-Score (pre-revenue companies fail it by construction), and DCFs built on management's peak-sales claims
- *Read:* runway < 6 quarters means a raise is near. Rough base rates to approval from industry clinical-success studies (BIO / Informa, all indications): Phase 1 ≈ 8–10%, Phase 2 ≈ 15%, Phase 3 ≈ 50–60%, filed (NDA/BLA) ≈ 90%; oncology runs lower. Risk-adjust every pipeline value by them and hand the dates to `catalyst-calendar`

**saas**
- *Swap in:* ARR and ARR growth · net revenue retention (NRR) and gross revenue retention (GRR) · Rule of 40 (revenue growth % + FCF margin %) · CAC payback (months) = S&M / (net-new ARR × gross margin) × 12 · subscription gross margin · SBC-adjusted FCF margin · RPO and current RPO (cRPO) growth vs. revenue growth
- *Ignore:* GAAP P/E for early-stage names, EV/EBITDA that adds back SBC, headline FCF margin without deducting SBC, current ratio (deferred revenue inflates current liabilities)
- *Read:* NRR > 110% strong, < 100% means the base is shrinking; GRR > 90%; Rule of 40 ≥ 40 on the SBC-adjusted margin; CAC payback < 24 months; cRPO growing slower than revenue is a leading deceleration signal

**How the pack changes the rest of the analysis.** Valuation switches to the sector multiple (P/TBV, P/B, P/AFFO, risk-adjusted pipeline value, EV/ARR or EV/revenue vs. growth); quality uses the sector KPIs in place of the generic margin and ratio checks; risk adds the sector's failure mode (deposit flight and rate marks for banks, reserve inadequacy for insurers, refinancing and occupancy for REITs, trial failure and dilution for biotech, retention decay for SaaS). Everything else — data verification, thesis invalidation and the signal block — is unchanged. State in the output which generic metrics were dropped and why.

---

## Step-by-Step Analysis Framework

### Phase 1: Document Orientation

Before diving into numbers, understand what kind of document this is and what period it covers:

- **Filing Type**: 10-K (annual), 10-Q (quarterly), 8-K (material event), DEF 14A (proxy), S-1 (IPO)
- **Fiscal Period**: Year-end or quarter-end date, fiscal year convention
- **Auditor**: External auditor name and audit opinion type (unqualified, qualified, adverse, disclaimer)
- **Auditor Change**: Any change in auditor is a major red flag — investigate immediately
- **Filing Date**: Note if filed late (extension requests = warning signal)
- **Restatements**: Any prior period restatements disclosed in current filing

---

### Phase 2: Management Discussion & Analysis (MD&A) Deep Read

The MD&A is management's own narrative explanation of results. Read it critically — management has incentives to highlight positives and minimize negatives.

**2.1 Revenue Analysis**

Extract and analyze from MD&A:

```
Revenue Breakdown Table:
Segment/Product Line    Current Period    Prior Period    YoY Change %    Commentary
─────────────────────────────────────────────────────────────────────────────────────
[Segment 1]
[Segment 2]
[Geographic: Americas]
[Geographic: EMEA]
[Geographic: APAC]
─────────────────────────────────────────────────────────────────────────────────────
Total Revenue
```

Key questions to answer from MD&A:
- What does management cite as the primary growth drivers? Are these sustainable or one-time?
- Is growth organic (volume/price) or inorganic (acquisitions)? Separate these explicitly.
- What is the mix shift between high-margin and low-margin products/services?
- Is management guiding to acceleration or deceleration? Are they vague or specific?
- What is the backlog, remaining performance obligations (RPO), or deferred revenue trend?

**2.2 Margin Analysis**

```
Margin Trend Table:
Metric              Current Period    Prior Period    QoQ or YoY    Explanation from MD&A
──────────────────────────────────────────────────────────────────────────────────────
Gross Margin %
Operating Margin %
Net Margin %
Adjusted EBITDA %   (if disclosed)
FCF Margin %        (Operating CF - Capex)
──────────────────────────────────────────────────────────────────────────────────────
```

Red flags in margin discussion:
- Non-GAAP exclusions growing faster than GAAP expenses (SBC, restructuring)
- Gross margin compression attributed to "product mix" without specifics
- COGS increases described only in absolute terms, not as % of revenue
- Operating leverage claims not reflected in actual operating margin expansion

**2.3 Liquidity and Capital Resources**

From the Liquidity section of MD&A, extract:
- Cash and equivalents position (end of period)
- Revolving credit facility (drawn / undrawn capacity)
- Upcoming debt maturities (12-month and 3-year look-ahead)
- Operating cash flow generated in period
- Free cash flow (OCF minus capex)
- Capital allocation priorities stated by management
- Share repurchase authorization remaining
- Dividend policy changes

**2.4 Forward-Looking Statements Analysis**

Catalog management's specific guidance language:

```
Guidance Item         Specific Language Used        Strength (Specific/Vague/Hedged)
────────────────────────────────────────────────────────────────────────────────────
Revenue Guidance
Margin Guidance
Capex Guidance
Hiring/Headcount
Product Launch Timing
────────────────────────────────────────────────────────────────────────────────────
```

Flag: When management shifts from specific numerical guidance to directional language ("we expect continued growth"), this is a meaningful signal of reduced confidence.

---

### Phase 3: Financial Statement Deep Dive

**3.1 Income Statement Quality Assessment**

```
Line Item Analysis:
                    Current    Prior    Change    Quality Note
Revenue             $          $        %
COGS                $          $        %
Gross Profit        $          %GP
R&D                 $          %Rev
S&M                 $          %Rev
G&A                 $          %Rev
Operating Income    $          %OM
Interest Expense    $          $
Tax Rate            %          %
Net Income (GAAP)   $
EPS (GAAP)          $
Non-GAAP EPS        $         Reconciliation items: ___
```

Quality checks:
- **Revenue recognition policy**: Has it changed? Check footnotes for ASC 606 adoption details
- **Channel stuffing signals**: Receivables growing faster than revenue (days sales outstanding expanding)
- **Deferred revenue**: Growing (positive — customers paying ahead) or shrinking (negative)
- **Tax rate**: Unusually low tax rate often driven by one-time benefits; normalize for comparison

**3.2 Balance Sheet Analysis**

```
Balance Sheet Health Check:
Asset Quality:
  Cash & Equivalents:         $___  (% of total assets)
  Accounts Receivable:        $___  DSO: ___ days  (vs. prior: ___)
  Inventory:                  $___  DIO: ___ days  (vs. prior: ___)
  Goodwill & Intangibles:     $___  (% of total assets) — impairment risk?
  Other Long-Term Assets:     $___

Liability Structure:
  Short-Term Debt:            $___  (due within 12 months)
  Long-Term Debt:             $___
  Total Debt:                 $___
  Net Debt/(Cash):            $___
  Interest Coverage Ratio:    ___x  (EBIT / Interest Expense)
  Debt/EBITDA:                ___x

Equity Quality:
  Retained Earnings Trend:    Growing / Declining / Negative
  Treasury Stock:             $___  (buyback history)
  AOCI:                       $___  (pension obligations, FX hedges)
```

Balance sheet red flags:
- Goodwill > 30% of total assets without clear acquisition rationale
- Accounts receivable growing 2x+ faster than revenue (aggressive recognition)
- Inventory build in a demand-softening environment
- Off-balance sheet operating lease obligations (check footnotes — ASC 842)
- Underfunded pension liabilities buried in AOCI

**3.3 Cash Flow Statement — The Truth Teller**

The cash flow statement is the hardest to manipulate. Always reconcile GAAP net income to operating cash flow:

```
Cash Flow Quality Analysis:
Operating Cash Flow:          $___
Less: Capex:                  $___
Free Cash Flow:               $___  FCF Margin: __%
FCF Conversion Rate:          ___   (FCF / Net Income — should be >80% for quality businesses)

Working Capital Changes:
  AR Change (use/source):     $___
  Inventory Change:           $___
  AP Change:                  $___
  Deferred Revenue Change:    $___
  Net Working Capital Impact: $___

SBC Add-Back:                 $___  (% of Revenue — >5% is dilutive)
D&A Add-Back:                 $___  (% of Revenue — maintenance capex proxy)
```

Cash flow quality flags:
- FCF significantly below net income (earnings quality problem)
- Large working capital builds consuming cash (inventory/AR growth)
- SBC >5% of revenue — real dilution not reflected in GAAP net income
- Capex below depreciation for multiple years (under-investment in assets)

---

### Phase 4: Risk Factors Analysis

The Risk Factors section (Item 1A in 10-K) is legally required to disclose material risks. Read for:

**4.1 New vs. Removed Risk Factors**

Compare current filing's risk factors against the prior period:

```
Risk Factor Changes:
NEW Risks Added (first appearance):
  1. [Risk title] — [Category: Business/Regulatory/Macro/Competition/Cyber/Legal]
  2. ...

REMOVED Risks (previously disclosed, now gone):
  1. [What was removed] — [Why might this be significant?]

ELEVATED Risks (same risk, but expanded disclosure or moved higher in list):
  1. [Risk title] — [What changed in the language]
```

Risk categories to flag as highest priority:
- **Regulatory/Legal**: New government investigations, pending litigation, regulatory changes
- **Customer Concentration**: Single customer >10% of revenue disclosed
- **Technology/Competition**: Specific competitor named as existential threat
- **Going Concern**: Doubt about ability to continue as a going concern (immediate red flag)
- **Debt Covenant**: Risk of violating debt covenants disclosed
- **Cybersecurity**: New material cyber incident disclosures (Item 1.05 of 8-K)

**4.2 Litigation and Legal Proceedings**

From footnotes and Item 3 (Legal Proceedings):
- Active lawsuits with >$X million exposure
- SEC or DOJ investigations
- Tax disputes and uncertain tax positions
- Environmental liabilities
- Patent litigation (key for tech and pharma)

---

### Phase 5: Accounting Policy and Footnote Analysis

Footnotes contain what management would prefer investors not to focus on.

**5.1 Critical Accounting Estimates**

Management must disclose "critical accounting estimates" — areas where judgment most affects reported results:

```
Critical Estimate Review:
  Revenue Recognition:   [Policy and any changes]
  Goodwill Impairment:   [Testing methodology, headroom]
  Stock-Based Comp:      [Fair value models, assumptions]
  Deferred Tax Assets:   [Valuation allowance — any new allowances = warning]
  Contingent Liabilities: [What is and isn't accrued]
  Pension/OPEB:          [Return assumption, discount rate]
```

**5.2 Related Party Transactions**

Any transactions between the company and executives, board members, or major shareholders. These require heightened scrutiny for potential conflicts of interest.

**5.3 Segment Reporting**

When companies add or remove reporting segments, investigate:
- Was a previously disclosed segment merged with another? (Often hides underperformance)
- Were goodwill allocations shifted between segments? (Can delay impairment)
- New segment disclosures can reveal previously hidden growth drivers

---

### Phase 6: Management Tone and Language Analysis

Apply natural language analysis to management's own words:

**6.1 Tone Scoring**

Rate management's tone across key sections:

```
Tone Assessment:
Section              Tone Score (1=Very Negative → 5=Very Positive)    Key Language
──────────────────────────────────────────────────────────────────────────────────
MD&A Overview
Revenue Discussion
Margin Discussion
Guidance Language
Risk Factors Framing
CEO Letter (if present)
──────────────────────────────────────────────────────────────────────────────────
Overall Tone:        [Score] / 5
Change vs. Prior:    More Positive / Same / More Negative
```

**6.2 Hedging Language Flags**

Flag specific hedging phrases that indicate uncertainty:
- "We believe" / "we expect" / "we anticipate" — standard forward-looking
- "We cannot assure" / "there can be no assurance" — heightened uncertainty
- "Significant uncertainty" / "material uncertainty" — near-crisis language
- Passive voice for negative news ("challenges were experienced") vs. active voice for positives
- Increasing use of "headwinds," "challenging environment," "softness"

**6.3 Management Credibility Tracking**

```
Guidance Accuracy Scorecard (prior 4 quarters):
Period    Revenue Guidance    Actual    Beat/Miss    Margin Guidance    Actual    Beat/Miss
Q-4
Q-3
Q-2
Q-1
──────────────────────────────────────────────────────────────────────────────────────────
Batting Average: ___  Beat Rate: ___  Avg. Miss: ___
```

---

### Phase 7: Year-over-Year Comparison (for Quarterly Reports)

For 10-Q analysis, compare against the same quarter prior year AND the sequential prior quarter:

```
YoY and Sequential Comparison:
Metric          Current Q    Prior Q (seq)    Prior Year Q    YoY %    QoQ %
Revenue
Gross Margin
Operating Income
EPS (GAAP)
FCF
```

Identify if trends are:
- Accelerating (sequential improvement + YoY beats)
- Stable (sequential flat, YoY in-line)
- Decelerating (sequential miss, YoY still positive)
- Deteriorating (both sequential and YoY misses)

---

### Phase 8: Insider Activity (from Proxy/Form 4 Data)

Cross-reference with available SEC Form 4 data around the filing date:
- CEO/CFO buying on the open market (strong signal — insiders rarely buy for tax purposes)
- Bulk insider selling at prices below historical averages (negative signal)
- New 10b5-1 plan adoptions (scheduled selling — less informative than open market)
- Executive departures disclosed in proxy or 8-K (CFO exits especially significant)

---

## Output Format

### Executive Summary (1-2 paragraphs)

High-level verdict on the filing quality and key takeaways for investors. Address: Is this a better or worse filing than prior periods? What is the single most important thing an investor should take away?

### Financial Health Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│  FINANCIAL REPORT ANALYSIS — [TICKER] [Filing Type] [Period]   │
├────────────────────────┬────────────────────────────────────────┤
│ Revenue Growth         │ [%] YoY   [Organic vs. Acquired]       │
│ Gross Margin           │ [%]  (vs. prior: [%]  Δ [bps])         │
│ Operating Margin       │ [%]  (vs. prior: [%]  Δ [bps])         │
│ FCF Margin             │ [%]  (FCF Conversion: [%])              │
│ Net Debt / (Cash)      │ $[M]  (Debt/EBITDA: [x])               │
│ DSO                    │ [days]  (vs. prior: [days])             │
│ Management Tone        │ [Positive / Neutral / Cautious]         │
├────────────────────────┼────────────────────────────────────────┤
│ Filing Quality Score   │ [Score] / 10                           │
│ Earnings Quality Score │ [Score] / 10                           │
│ Balance Sheet Score    │ [Score] / 10                           │
└────────────────────────┴────────────────────────────────────────┘
```

### Key Insights (Bulleted)

**Positives (Bullish Signals):**
- [Specific insight with page/section reference from filing]

**Negatives (Bearish Signals):**
- [Specific insight with page/section reference from filing]

**Neutral / Watch Items:**
- [Items requiring monitoring but not yet actionable]

### Red Flags and Anomalies

| # | Red Flag | Severity | Where Found | Implication |
|---|----------|----------|-------------|-------------|
| 1 | | HIGH/MED/LOW | | |

### Accounting Quality Score

| Criterion | Score (0–3) | Notes |
|-----------|-------------|-------|
| Revenue recognition clarity | | |
| Non-GAAP reconciliation quality | | |
| FCF conversion rate | | |
| Working capital trends | | |
| Footnote transparency | | |
| Auditor opinion | | |
| Related party transactions | | |
| **Total** | **/21** | |

Score guide: 18–21 = High quality | 12–17 = Average | <12 = Scrutinize further

---

## Input Formats Accepted

```bash
# Paste raw text from 10-K or 10-Q sections
/financial-report-analyst [paste filing text]

# Analyze specific section of a recent filing
/financial-report-analyst AAPL 10-K --section md&a
/financial-report-analyst MSFT 10-Q --section risk-factors
/financial-report-analyst NVDA 10-K --section cash-flow

# Full report analysis (all sections)
/financial-report-analyst GOOGL 10-K --full

# Compare current vs prior filing
/financial-report-analyst META 10-K --compare-prior

# Quick earnings press release analysis
/financial-report-analyst AMZN --press-release [paste text]

# Proxy statement analysis
/financial-report-analyst TSLA --proxy
```

---

## Thesis Invalidation

After delivering the analysis signal, specify what would reverse it:

**If signal is BULLISH — thesis breaks if:**
- auditor issues going concern warning OR material restatement announced
- [One or two more triggers drawn from this analysis's own drivers, each with a threshold]

**If signal is BEARISH — thesis breaks if:**
- new auditor clears all concerns AND restatement resolved favorably
- [One or two more triggers drawn from this analysis's own drivers, each with a threshold]

**Re-run this analysis when:**
- [ ] Next earnings release
- [ ] Price moves ±15% from current level
- [ ] 60 days have elapsed
- [ ] Material news event (acquisition, leadership change, regulatory decision)

## Standard Signal Output

All analysis concludes with this standardized block:

In the output, the box below is followed immediately by this machine-readable footer — the same values as the box, filled in (no placeholders, no comments), so tools can read the result without parsing the box:

```json
{"investskill": "1", "skill": "financial-report-analyst", "ticker": "<TICKER, or null for a portfolio / market-wide view>", "as_of": "<YYYY-MM-DD from Data & Sources>", "signal": "<BULLISH | NEUTRAL | BEARISH>", "confidence": "<HIGH | MEDIUM | LOW>", "horizon": "<SHORT-TERM | MEDIUM-TERM | LONG-TERM>", "score": 0.0, "action": "<BUY | HOLD | SELL>", "conviction": "<STRONG | MODERATE | WEAK>", "retrieval": "<pasted by user | web/tool retrieval | model memory>", "sources": ["<each primary source, dated>"]}
```

```
╔══════════════════════════════════════════════╗
║              INVESTMENT SIGNAL               ║
╠══════════════════════════════════════════════╣
║ Signal:      BULLISH / NEUTRAL / BEARISH     ║
║ Confidence:  HIGH / MEDIUM / LOW             ║
║ Horizon:     SHORT / MEDIUM / LONG-TERM      ║
║ Score:       X.X / 10                        ║
╠══════════════════════════════════════════════╣
║ Action:      BUY / HOLD / SELL               ║
║ Conviction:  STRONG / MODERATE / WEAK        ║
╚══════════════════════════════════════════════╝
```

Score Guide: 8.0–10.0 Strongly Bullish | 6.0–7.9 Moderately Bullish | 4.0–5.9 Neutral | 2.0–3.9 Moderately Bearish | 0.0–1.9 Strongly Bearish
Confidence: HIGH (strong data, clear signals) | MEDIUM (mixed signals) | LOW (limited data, conflicting signals)
Horizon: SHORT-TERM (1 week–3 months) | MEDIUM-TERM (3 months–1 year) | LONG-TERM (1+ years)

**Disclaimer:** Educational analysis only. Not financial advice.
