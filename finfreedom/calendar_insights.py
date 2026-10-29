from datetime import date
from finfreedom.database import connect
from finfreedom.research_data import INDEX_CATALOG, cached as research_cached

def calendar_insights(date: date):
    """Read cached index, watchlist and market-flow observations for one trading date."""
    calendar_index_ids = {"INDEX:SH000001", "INDEX:SZ399001", "INDEX:SH000300", "INDEX:SZ399006",
                          "INDEX:HSI", "INDEX:SPX", "INDEX:NASDAQ", "INDEX:DJIA"}
    index_rows = []
    for meta in INDEX_CATALOG:
        if meta["id"] not in calendar_index_ids:
            continue
        payload = research_cached(connect, "index", meta["id"]) or {}
        rows = payload.get("rows", [])
        position = next((i for i, row in enumerate(rows) if str(row.get("bar_time", ""))[:10] == date.isoformat()), -1)
        previous = next((row for row in reversed(rows[:position]) if float(row.get("close") or 0) > 0), None) if position >= 0 else None
        current = rows[position] if position >= 0 else None
        value = float(current["close"]) / float(previous["close"]) - 1 if current and previous else None
        index_rows.append({**meta, "change_percent": value * 100 if value is not None else None,
                           "close": current.get("close") if current else None,
                           "source": payload.get("source"), "state": payload.get("state", "waiting")})
    watch_rows = []
    with connect() as conn:
        watched = conn.execute("SELECT w.instrument_id, q.name, q.market FROM watchlist w LEFT JOIN quotes q ON q.instrument_id=w.instrument_id ORDER BY w.added_at DESC LIMIT 12").fetchall()
        for item in watched:
            current = conn.execute("SELECT close FROM bars WHERE instrument_id=? AND interval_name='1d' AND adjustment='none' AND bar_time=?", (item["instrument_id"], date.isoformat())).fetchone()
            previous = conn.execute("SELECT close,bar_time FROM bars WHERE instrument_id=? AND interval_name='1d' AND adjustment='none' AND bar_time<? ORDER BY bar_time DESC LIMIT 1", (item["instrument_id"], date.isoformat())).fetchone()
            change = (float(current["close"]) / float(previous["close"]) - 1) * 100 if current and previous and previous["close"] else None
            watch_rows.append({"instrument_id": item["instrument_id"], "name": item["name"] or item["instrument_id"],
                               "market": item["market"], "change_percent": change,
                               "close": current["close"] if current else None})
    flow = research_cached(connect, "market_flow", "CN") or {}
    flow_row = next((row for row in flow.get("rows", []) if str(row.get("日期", row.get("date", row.get("日期时间", ""))))[:10] == date.isoformat()), None)
    return {"date": date.isoformat(), "indices": index_rows, "watchlist": watch_rows,
            "market_flow": {"row": flow_row, "source": flow.get("source"), "state": flow.get("state", "waiting"),
                            "note": flow.get("note")},
            "connect_flow": {"northbound": None, "southbound": None,
            "note": "实时北向买卖额与总额已停止发布；交易所仍提供日终统计产品。本工作台尚未接入互联互通日终数据源。"}}
