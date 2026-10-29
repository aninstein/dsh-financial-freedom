"""Owner-scoped holdings snapshots and review drafts.

Validation is adapted from the Financial Freedom holdings domain. Image
understanding now belongs to the DSH Agent; this module never calls a model.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from finfreedom.database import connect

CURRENCIES = {"CNY", "HKD", "USD"}
INSTRUMENT = re.compile(r"^(CN|HK|US|FUND|GOLD):[A-Z0-9._-]{1,48}$", re.I)


class Position(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    instrument_id: str | None = Field(default=None, max_length=64)
    name: str = Field(min_length=1, max_length=80)
    asset_class: str
    quantity: float | None = Field(default=None, gt=0, le=1_000_000_000)
    cost_basis: float | None = Field(default=None, ge=0, le=1_000_000_000_000)
    manual_value: float | None = Field(default=None, ge=0, le=1_000_000_000_000)
    reported_return_pct: float | None = Field(default=None, ge=-100, le=100_000)


class Snapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    principal: float | None = Field(default=None, ge=0, le=1_000_000_000_000)
    cash: float | None = Field(default=None, ge=0, le=1_000_000_000_000)
    expected_updated_at: str | None = None
    positions: list[Position] = Field(default_factory=list, max_length=500)


def _currency(value: str) -> str:
    result = value.upper()
    if result not in CURRENCIES:
        raise ValueError("仅支持 CNY、HKD、USD，暂不混合换算。")
    return result


def _normalize_position(position: Position, currency: str, allow_incomplete: bool) -> dict[str, Any]:
    item = position.model_dump()
    item["name"] = item["name"].strip()
    if not item["name"]:
        raise ValueError("持仓名称不能为空")
    if item["asset_class"] not in {"stock", "fund", "gold"}:
        raise ValueError("资产类别必须是 stock、fund 或 gold")
    if item["quantity"] is None and item["manual_value"] is None and not allow_incomplete:
        raise ValueError(f"{item['name']}缺少份额和资料市值，请至少填写一项。")
    code = item["instrument_id"]
    if code:
        market, separator, symbol = code.strip().partition(":")
        market = market.upper()
        if not separator:
            raise ValueError(f"{item['name']}缺少市场前缀代码")
        if market == "HK" and symbol.isdigit() and len(symbol) <= 5:
            symbol = symbol.zfill(5)
        code = f"{market}:{symbol if market == 'GOLD' else symbol.upper()}"
        if not INSTRUMENT.fullmatch(code):
            raise ValueError(f"标的代码格式不正确：{code[:64]}")
        if ((item["asset_class"] == "gold" and market not in {"GOLD", "FUND"})
                or (item["asset_class"] == "fund" and market not in {"FUND", "CN"})
                or (item["asset_class"] == "stock" and market not in {"CN", "HK", "US"})):
            raise ValueError(f"资产类别与标的代码不匹配：{code}")
        if ((currency == "CNY" and market in {"HK", "US"})
                or (currency == "HKD" and market != "HK")
                or (currency == "USD" and market != "US")):
            raise ValueError(f"标的与当前账户币种不匹配：{code}")
    elif not allow_incomplete:
        raise ValueError(f"{item['name']}缺少标的代码")
    item["instrument_id"] = code
    return item


def portfolios(owner_id: str, currency: str | None = None) -> list[dict[str, Any]]:
    with connect() as db:
        if currency:
            rows = db.execute("SELECT * FROM personal_portfolios WHERE owner_id=? AND currency=? ORDER BY currency",
                              (owner_id, _currency(currency))).fetchall()
        else:
            rows = db.execute("SELECT * FROM personal_portfolios WHERE owner_id=? ORDER BY currency", (owner_id,)).fetchall()
        result = []
        for raw in rows:
            portfolio = {key: value for key, value in dict(raw).items() if key != "owner_id"}
            positions = db.execute("SELECT p.*, q.last, q.currency AS quote_currency, q.received_at AS quote_time, q.provider, q.freshness FROM personal_positions p LEFT JOIN quotes q ON q.instrument_id=p.instrument_id WHERE p.owner_id=? AND p.currency=? ORDER BY p.asset_class,p.instrument_id",
                                   (owner_id, portfolio["currency"])).fetchall()
            from finfreedom import futu_data
            live = {row.get("instrument_id"): row for row in futu_data.watchlist().get("rows", []) if row.get("quote_available")}
            items = []
            for position in positions:
                item = {key: value for key, value in dict(position).items() if key != "owner_id"}
                quote = live.get(item["instrument_id"])
                if quote and quote.get("currency") == portfolio["currency"]:
                    item.update(last=quote.get("last"), quote_currency=quote.get("currency"),
                                quote_time=quote.get("received_at"), provider="富途 OpenD", freshness=quote.get("freshness"))
                usable = item.get("last") is not None and item.get("quantity") is not None and item.get("quote_currency") == portfolio["currency"]
                item["current_value"] = round(item["quantity"] * item["last"], 2) if usable else item["manual_value"]
                item["valuation_source"] = "行情" if usable else "手动" if item["current_value"] is not None else "缺失"
                items.append(item)
            portfolio["positions"] = items
            portfolio["valuation_complete"] = all(p["current_value"] is not None for p in items)
            portfolio["holdings_value"] = (round(sum(float(p["current_value"]) for p in items), 2)
                                             if portfolio["valuation_complete"] else None)
            portfolio["total_assets"] = (round(portfolio["holdings_value"] + portfolio["cash"], 2)
                                          if portfolio["holdings_value"] is not None and portfolio["cash"] is not None else None)
            result.append(portfolio)
        return result


def replace_snapshot(owner_id: str, currency: str, raw: dict[str, Any]) -> dict[str, Any]:
    currency = _currency(currency)
    snapshot = Snapshot.model_validate(raw)
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position in snapshot.positions:
        item = _normalize_position(position, currency, allow_incomplete=False)
        if item["instrument_id"] in seen:
            raise ValueError(f"同一币种内不能重复登记：{item['instrument_id']}")
        seen.add(item["instrument_id"])
        cleaned.append(item)
    if snapshot.principal is None and snapshot.cash is None and not cleaned:
        raise ValueError("请至少填写账户本金、现金或一条持仓。")
    with connect() as db:
        previous = db.execute("SELECT updated_at FROM personal_portfolios WHERE owner_id=? AND currency=?",
                              (owner_id, currency)).fetchone()
        prior_version = previous["updated_at"] if previous else None
        if prior_version != snapshot.expected_updated_at:
            raise RuntimeError("持仓已更新或尚未读取当前版本，请先重新读取后再修改。")
        if previous:
            from finfreedom.holdings_performance import record_snapshot
            record_snapshot(db, owner_id, currency)
        stamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
        if previous:
            db.execute("UPDATE personal_portfolios SET principal=?,cash=?,updated_at=? WHERE owner_id=? AND currency=?",
                       (snapshot.principal, snapshot.cash, stamp, owner_id, currency))
        else:
            db.execute("INSERT INTO personal_portfolios(owner_id,currency,principal,cash,updated_at) VALUES(?,?,?,?,?)",
                       (owner_id, currency, snapshot.principal, snapshot.cash, stamp))
        db.execute("DELETE FROM personal_positions WHERE owner_id=? AND currency=?", (owner_id, currency))
        for item in cleaned:
            db.execute("""INSERT INTO personal_positions
                (owner_id,currency,instrument_id,name,asset_class,quantity,cost_basis,manual_value,updated_at,reported_return_pct)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (owner_id, currency, item["instrument_id"], item["name"], item["asset_class"], item["quantity"],
                 item["cost_basis"], item["manual_value"], stamp, item["reported_return_pct"]))
        from finfreedom.holdings_performance import record_snapshot
        record_snapshot(db, owner_id, currency, stamp)
    return portfolios(owner_id, currency)[0]


def update_positions(owner_id: str, currency: str, positions: list[dict[str, Any]], expected_updated_at: str | None) -> dict[str, Any]:
    """Merge explicitly supplied fields into one currency without dropping unrelated holdings."""
    currency = _currency(currency)
    if not isinstance(positions, list) or not 1 <= len(positions) <= 500:
        raise ValueError('请提供需要录入或更新的持仓')
    with connect() as db:
        account = db.execute('SELECT principal,cash,updated_at FROM personal_portfolios WHERE owner_id=? AND currency=?', (owner_id,currency)).fetchone()
        existing = db.execute('SELECT instrument_id,name,asset_class,quantity,cost_basis,manual_value,reported_return_pct FROM personal_positions WHERE owner_id=? AND currency=?', (owner_id,currency)).fetchall()
    version = account['updated_at'] if account else None
    if version != expected_updated_at:
        raise RuntimeError('持仓已更新，请重新读取后再修改。')
    entries = {row['instrument_id']:dict(row) for row in existing}
    allowed = set(Position.model_fields)
    seen=set()
    for item in positions:
        if not isinstance(item,dict) or set(item)-allowed: raise ValueError('持仓字段无效')
        raw = str(item.get('instrument_id') or '').strip()
        market, _, symbol = raw.partition(':')
        market = market.upper()
        if market == 'HK' and symbol.isdigit() and len(symbol) <= 5: symbol = symbol.zfill(5)
        code = market + ':' + (symbol if market == 'GOLD' else symbol.upper())
        if not INSTRUMENT.fullmatch(code) or code in seen: raise ValueError('请提供不重复的有效标的代码')
        seen.add(code)
        supplied = {k:v for k,v in item.items() if v is not None}
        entries[code] = {**entries.get(code, {}), **supplied, 'instrument_id':code}
    snapshot={'expected_updated_at':version,'principal':account['principal'] if account else None,
              'cash':account['cash'] if account else None,'positions':list(entries.values())}
    return replace_snapshot(owner_id,currency,snapshot)


def prepare_import(owner_id: str, currency: str, text: str | None,
                   positions: list[dict[str, Any]] | None, session_id: str | None = None,
                   source: str = "DSH 对话") -> dict[str, Any]:
    currency = _currency(currency)
    if (not text or not text.strip()) and not positions:
        raise ValueError("缺少持仓资料。请附上持仓截图或粘贴持仓文字，再由 DSH 识别后生成草稿。")
    if text and len(text) > 20_000:
        raise ValueError("持仓文字最多 20000 个字符")
    warnings: list[str] = []
    clean: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate((positions or [])[:100]):
        try:
            item = _normalize_position(Position.model_validate(row), currency, allow_incomplete=True)
            code = item["instrument_id"]
            if code and code in seen:
                raise ValueError("重复标的")
            if code:
                seen.add(code)
            else:
                warnings.append(f"{item['name']}：请核对并补充标的代码。")
            if item["quantity"] is None and item["manual_value"] is None:
                warnings.append(f"{item['name']}：请至少补充份额或资料市值。")
            clean.append(item)
        except (ValidationError, ValueError, TypeError):
            warnings.append(f"第 {index + 1} 条持仓信息无法确认，未加入草稿。")
    if positions and len(positions) > 100:
        warnings.append("超过 100 条的部分未纳入草稿。")
    if not clean and not text:
        raise ValueError("没有识别到可核对的持仓内容。")
    draft = {"currency": currency, "positions": clean, "source": source,
             "source_text": (text or "")[:20_000], "warnings": warnings[:20],
             "created_at": datetime.now(timezone.utc).isoformat()}
    draft_id = "HI-" + uuid.uuid4().hex[:16].upper()
    with connect() as db:
        db.execute("INSERT INTO holdings_import_drafts(draft_id,owner_id,session_id,currency,payload,created_at) VALUES(?,?,?,?,?,?)",
                   (draft_id, owner_id, session_id, currency, json.dumps(draft, ensure_ascii=False), draft["created_at"]))
    return {"draft_id": draft_id, "currency": currency, "count": len(clean),
            "positions": clean,
            "missing_code": sum(item["instrument_id"] is None for item in clean),
            "missing_quantity": sum(item["quantity"] is None for item in clean),
            "warnings": warnings[:20], "saved": False,
            "message": "这是待核对草稿；核对并补齐必需字段后，再通过持仓写入操作保存。"}


def get_import_draft(owner_id: str, draft_id: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT payload FROM holdings_import_drafts WHERE owner_id=? AND draft_id=?",
                         (owner_id, draft_id)).fetchone()
    if not row:
        raise KeyError("持仓草稿不存在")
    return json.loads(row["payload"])
