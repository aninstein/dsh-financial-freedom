"""Deterministic research queries migrated from the legacy MCP contract."""

from __future__ import annotations

from typing import Any

from finfreedom import cycle_analysis
from finfreedom.database import connect


def _evidence(kind: str, title: str, source: str, as_of: str | None,
              detail: dict[str, Any]) -> dict[str, Any]:
    return {"evidence_id": "E001", "type": kind, "title": title,
            "source": source, "as_of": as_of, "detail": detail}


async def execute(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Run a deliberately small set of read-only, locally deterministic tools."""
    if name == "get_watchlist":
        with connect() as db:
            rows = db.execute("""
                SELECT w.instrument_id, q.name, q.last, q.currency, q.exchange_time,
                       q.received_at, q.provider, q.freshness
                FROM watchlist w LEFT JOIN quotes q ON q.instrument_id=w.instrument_id
                ORDER BY w.added_at DESC LIMIT 8
            """).fetchall()
        data = {"instruments": [dict(row) for row in rows], "limit": 8,
                "note": "仅返回本机自选与缓存报价；报价须按来源时间与新鲜度核对。"}
        item = _evidence("watchlist", "最近自选与缓存报价", "本机 finfreedom 缓存", None, data)
        return {"evidence": [item], **data}

    if name == "search_instruments":
        query = str(args.get("query", "")).strip()[:80]
        if not query:
            raise ValueError("请输入股票名称或代码")
        with connect() as db:
            rows = db.execute("""
                SELECT instrument_id,name,symbol,market,last,currency,freshness
                FROM quotes WHERE name LIKE ? OR symbol LIKE ? OR instrument_id LIKE ?
                ORDER BY market,symbol LIMIT 10
            """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
        return {"matches": [dict(row) for row in rows],
                "note": "仅搜索本机已缓存的标的；无结果不代表该标的不存在。"}

    if name == "get_historical_cycles":
        instrument_id = str(args.get("instrument_id", "")).strip().upper()
        if not instrument_id or ":" not in instrument_id or len(instrument_id) > 64:
            raise ValueError("instrument_id 须使用 MARKET:SYMBOL 格式")
        try:
            years = int(args.get("years", 5))
        except (TypeError, ValueError) as exc:
            raise ValueError("years 须为 1 到 10 的整数") from exc
        data = cycle_analysis.analyze(connect, instrument_id, years)
        item = _evidence("historical_cycles", f"{instrument_id} 历史周期统计",
                         "finfreedom 本机日线确定性统计", data.get("last_bar"), data)
        return {"evidence": [item], **data}

    raise ValueError(f"研究工具 {name} 尚未迁移；请查看 catalog.implementation_status")
