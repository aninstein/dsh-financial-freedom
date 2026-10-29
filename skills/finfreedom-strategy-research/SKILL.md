---
name: finfreedom-strategy-research
description: Design and review reproducible market strategies and supported backtests, including data quality, costs, benchmarks and robustness.
---

# 策略与回测研究

先询问标的、市场、频率、规则、时间范围、基准和成本。结合 `finfreedom-research` 查询 catalog、日线数据与已保存回测；只使用当前工具明确支持的策略和参数，无法运行的策略应说明限制，不能伪造回测结果。

评估数据起止时间、复权、缺失交易日和幸存者偏差；区分样本内和样本外，检查信号滞后、防止未来函数，并描述手续费、滑点、成交限制与仓位假设。分析收益、最大回撤、风险和买入持有基准，能算则展示公式与数据集版本，不能算则写明。灵敏度和压力情景必须标为假设，不自动提交任何订单。
