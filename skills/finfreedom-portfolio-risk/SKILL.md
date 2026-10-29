---
name: finfreedom-portfolio-risk
description: Evaluate a finfreedom portfolio's exposures, concentration and risk scenarios using sourced owner-scoped data.
---

# 持仓与组合风险研究

结合 `finfreedom-research` 工作：先读取 `mcp__finfreedom__catalog`、相关投资记忆与当前币种 `holdings`；需要其他币种时分别读取，不隐式换汇。依据可验证的持仓数量、市值和数据时点，计算资产、单标的和行业集中度；缺少行业、成本、资金或估值时标明覆盖范围，不把未知值视为零。必要时调用市场、指数、标的及基金研究工具交叉核对。

风险情景要写清假设和作用范围，以敏感性分析而不是预测展示。没有真实因子、持仓历史或回报序列时，不声称计算了相关性、VaR、回撤或风险贡献。对持仓建议区分事实、判断、触发条件和反方证据；不得自行变更持仓、记忆或提交交易。
