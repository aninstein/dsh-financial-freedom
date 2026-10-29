"""Owner-scoped workspace state shared by the web UI and the built-in MCP.

Only user-authored calendar content and card presentation live here. Quotes,
research evidence, and portfolio valuations remain in their source tables.
"""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from finfreedom.paper import HTTPException


from finfreedom.database import connect

BUILTIN_CARDS = frozenset({"calendar", "watchlist", "markets", "gold", "indices", "news", "liquidity", "flows", "sectors", "research", "documents", "holdings", "security", "settings", "clock", "data"})
DEFAULT_CARDS = ["watchlist", "calendar", "clock", "data"]
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def initialize() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS owner_workspace_state (
            owner_id TEXT NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
            version INTEGER NOT NULL, updated_at TEXT NOT NULL,
            PRIMARY KEY(owner_id,kind)
        );
        """)


def _default(kind: str) -> dict[str, Any]:
    if kind == "guide":
        return {"mine": {}, "favorites": {}}
    if kind == "cards":
        return {"cards": DEFAULT_CARDS.copy(), "wide": False, "visible": True,
                "width": 320, "expanded_card": None, "custom_cards": {}, "overrides": {}}
    if kind == "calendar":
        return {"plans": [], "events": [], "subscriptions": [], "alarmAcknowledged": {}}
    raise ValueError("unknown workspace state")


def get_state(owner_id: str, kind: str) -> dict[str, Any]:
    with connect() as db:
        row = db.execute("SELECT payload,version,updated_at FROM owner_workspace_state WHERE owner_id=? AND kind=?", (owner_id, kind)).fetchone()
    if not row:
        return {**_default(kind), "version": 0, "updated_at": None}
    return {**json.loads(row["payload"]), "version": int(row["version"]), "updated_at": row["updated_at"]}


def _text(value: Any, label: str, maximum: int, *, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise HTTPException(422, f"{label}格式无效")
    return value.strip()


def _cards(value: dict[str, Any]) -> dict[str, Any]:
    customs = value.get("custom_cards", {})
    if not isinstance(customs, dict) or len(customs) > 30:
        raise HTTPException(422, "自定义卡片数量超限")
    clean_customs = {}
    for key, card in customs.items():
        if not isinstance(key, str) or not re.fullmatch(r"note:[a-f0-9]{12,32}", key) or not isinstance(card, dict):
            raise HTTPException(422, "卡片编号无效")
        clean_customs[key] = {"title": _text(card.get("title"), "卡片标题", 80, required=True),
                              "body": _text(card.get("body"), "卡片正文", 4000)}
    overrides = value.get("overrides", {})
    if not isinstance(overrides, dict) or len(overrides) > len(BUILTIN_CARDS):
        raise HTTPException(422, "卡片显示设置无效")
    clean_overrides = {}
    for key, item in overrides.items():
        if key not in BUILTIN_CARDS or not isinstance(item, dict):
            raise HTTPException(422, "卡片显示设置无效")
        clean_overrides[key] = {"title": _text(item.get("title", ""), "卡片标题", 80),
                                "note": _text(item.get("note", ""), "卡片附注", 600)}
    ids = value.get("cards", DEFAULT_CARDS)
    if not isinstance(ids, list) or len(ids) > 45 or any(not isinstance(x, str) or x not in BUILTIN_CARDS | clean_customs.keys() for x in ids) or len(ids) != len(set(ids)):
        raise HTTPException(422, "卡片顺序包含未知或重复卡片")
    expanded = value.get("expanded_card")
    if expanded is not None and expanded not in ids:
        raise HTTPException(422, "展开的卡片必须在右栏中")
    width = value.get("width", 320)
    if not isinstance(width, int) or isinstance(width, bool) or not 270 <= width <= 1200:
        raise HTTPException(422, "右栏宽度须为 270–1200 像素")
    return {"cards": ids, "wide": bool(value.get("wide", False)),
            "visible": bool(value.get("visible", True)), "width": width,
            "expanded_card": expanded, "custom_cards": clean_customs, "overrides": clean_overrides}


def _calendar(value: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for field, cap in (("plans", 500), ("events", 500), ("subscriptions", 100)):
        rows = value.get(field, [])
        if not isinstance(rows, list) or len(rows) > cap:
            raise HTTPException(422, f"{field}数量超限")
        clean = []
        seen = set()
        for row in rows:
            if not isinstance(row, dict):
                raise HTTPException(422, f"{field}记录无效")
            ident = _text(row.get("id"), "日历记录编号", 100, required=True)
            if ident in seen:
                raise HTTPException(422, "日历记录编号重复")
            seen.add(ident)
            item = {"id": ident}
            if field != "subscriptions":
                day = _text(row.get("date"), "日期", 10, required=True)
                if not DATE.fullmatch(day):
                    raise HTTPException(422, "日期格式无效")
                item["date"] = day
            at = row.get("time") or row.get("remindAt") or ""
            if at and (not isinstance(at, str) or not TIME.fullmatch(at)):
                raise HTTPException(422, "提醒时间格式无效")
            for key, maximum in (("time", 5), ("remindAt", 5), ("category", 40),
                                 ("title", 120), ("name", 80), ("text", 1200),
                                 ("detail", 1200), ("sourceUrl", 500),
                                 ("subscriptionId", 100), ("createdAt", 40)):
                if key in row and row[key] is not None:
                    item[key] = _text(row[key], key, maximum)
            if field == "subscriptions":
                item["enabled"] = bool(row.get("enabled", True))
            clean.append(item)
        result[field] = clean
    ack = value.get("alarmAcknowledged", {})
    if not isinstance(ack, dict) or len(ack) > 2000 or any(not isinstance(k, str) or len(k) > 150 or not isinstance(v, str) or len(v) > 40 for k, v in ack.items()):
        raise HTTPException(422, "提醒确认记录无效")
    recent = (datetime.now(timezone.utc).date() - timedelta(days=3)).isoformat()
    retained = {key: value for key, value in ack.items()
                if not key.startswith("daily:") or key.rsplit(":", 1)[-1] >= recent}
    if len(retained) > 500:
        raise HTTPException(422, "提醒确认记录超限，请清理旧事件")
    result["alarmAcknowledged"] = retained
    return result


def _guide(value: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for field in ("mine", "favorites"):
        entries = value.get(field, {})
        if not isinstance(entries, dict) or len(entries) > 500:
            raise HTTPException(422, "词条数量超限")
        result[field] = {}
        for ident, row in entries.items():
            if not isinstance(ident, str) or not re.fullmatch(r"(?:builtin-[a-zA-Z0-9_-]{1,64}|user-[a-f0-9]{32})", ident) or not isinstance(row, dict):
                raise HTTPException(422, "词条格式无效")
            text = row.get("markdown")
            if not isinstance(text, str) or not text.strip() or len(text) > 20000:
                raise HTTPException(422, "词条 Markdown 无效")
            group = row.get("group", "个人词条")
            if not isinstance(group, str) or len(group) > 100:
                raise HTTPException(422, "词条分类无效")
            result[field][ident] = {"markdown": text, "group": group}
    return result


def put_state(owner_id: str, kind: str, value: dict[str, Any], expected_version: int | None = None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise HTTPException(422, "工作台数据必须是对象")
    payload = _cards(value) if kind == "cards" else _calendar(value) if kind == "calendar" else _guide(value) if kind == "guide" else _default(kind)
    stamped = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    with connect() as db:
        lock = "" if isinstance(db, sqlite3.Connection) else " FOR UPDATE"
        row = db.execute("SELECT version FROM owner_workspace_state WHERE owner_id=? AND kind=?" + lock, (owner_id, kind)).fetchone()
        version = int(row["version"]) if row else 0
        if expected_version is not None and version != expected_version:
            raise HTTPException(409, "工作台内容已更新，请刷新后再修改")
        if row:
            db.execute("UPDATE owner_workspace_state SET payload=?,version=?,updated_at=? WHERE owner_id=? AND kind=?",
                       (json.dumps(payload, ensure_ascii=False), version + 1, stamped, owner_id, kind))
        else:
            db.execute("INSERT INTO owner_workspace_state(owner_id,kind,payload,version,updated_at) VALUES(?,?,?,?,?)",
                       (owner_id, kind, json.dumps(payload, ensure_ascii=False), 1, stamped))
    return {**payload, "version": version + 1, "updated_at": stamped}


def add_note_card(owner_id: str, title: str, body: str) -> dict[str, Any]:
    state = get_state(owner_id, "cards")
    ident = "note:" + uuid.uuid4().hex[:16]
    state["custom_cards"][ident] = {"title": title, "body": body}
    state["cards"].append(ident)
    return {"id": ident, "state": put_state(owner_id, "cards", state, state["version"])}




def mutate(owner_id: str, resource: str, action: str, data: dict[str, Any]) -> Any:
    from finfreedom import workspace_state as workspace
    if resource == "cards":
        state = workspace.get_state(owner_id, "cards")
        expected = data.get("expected_version")
        if expected is None or expected != state["version"]:
            raise workspace.HTTPException(409, "先读取当前卡片版本，再提交修改")
        if action == "set_layout":
            for key in ("cards", "wide", "visible", "width", "expanded_card"):
                if key in data:
                    state[key] = data[key]
        elif action == "create_note":
            import uuid
            ident = "note:" + uuid.uuid4().hex[:16]
            state["custom_cards"][ident] = {"title": data.get("title", ""), "body": data.get("body", "")}
            state["cards"].append(ident)
        elif action in {"update_note", "delete_note"}:
            ident = str(data.get("id", ""))
            if ident not in state["custom_cards"]:
                raise workspace.HTTPException(404, "自定义卡片不存在")
            if action == "delete_note":
                del state["custom_cards"][ident]
                state["cards"] = [x for x in state["cards"] if x != ident]
                if state.get("expanded_card") == ident:
                    state["expanded_card"] = None
            else:
                state["custom_cards"][ident].update({k: data[k] for k in ("title", "body") if k in data})
        elif action == "set_builtin_note":
            ident = str(data.get("id", ""))
            if ident not in workspace.BUILTIN_CARDS:
                raise workspace.HTTPException(404, "内置卡片不存在")
            state["overrides"][ident] = {"title": data.get("title", ""), "note": data.get("note", "")}
        else:
            raise workspace.HTTPException(422, "未知卡片操作")
        return workspace.put_state(owner_id, "cards", state, expected)
    if resource == "calendar":
        state = workspace.get_state(owner_id, "calendar")
        expected = data.get("expected_version")
        if expected is None or expected != state["version"]:
            raise workspace.HTTPException(409, "先读取当前日历版本，再提交修改")
        kind = str(data.get("kind", ""))
        collection = {"plan": "plans", "event": "events", "subscription": "subscriptions"}.get(kind)
        if action in {"create", "update", "delete"} and not collection:
            raise workspace.HTTPException(422, "kind 须为 plan/event/subscription")
        if action == "create":
            import uuid
            item = dict(data.get("item") or {})
            item["id"] = uuid.uuid4().hex
            item.setdefault("createdAt", datetime.now(timezone.utc).isoformat())
            state[collection].append(item)
        elif action in {"update", "delete"}:
            ident = str(data.get("id", ""))
            if not any(x["id"] == ident for x in state[collection]):
                raise workspace.HTTPException(404, "日历记录不存在")
            if action == "delete":
                state[collection] = [x for x in state[collection] if x["id"] != ident]
            else:
                patch = dict(data.get("patch") or {})
                patch.pop("id", None)
                state[collection] = [{**x, **patch} if x["id"] == ident else x for x in state[collection]]
        elif action == "acknowledge":
            state["alarmAcknowledged"][str(data.get("id", ""))] = datetime.now(timezone.utc).isoformat()
        else:
            raise workspace.HTTPException(422, "未知日历操作")
        return workspace.put_state(owner_id, "calendar", state, expected)
    raise ValueError("未知工作台操作")
