"""DSH adapter for the original local paper broker; no real brokerage orders."""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
from .database import active_profile, connect
from . import paper, futu_data

SCHEMA = '''
CREATE TABLE IF NOT EXISTS paper_accounts(account_id TEXT PRIMARY KEY,label TEXT NOT NULL,currency TEXT NOT NULL,initial_cash REAL NOT NULL,created_at TEXT NOT NULL,market TEXT NOT NULL,owner_id TEXT,state TEXT NOT NULL DEFAULT 'active',replaces_account_id TEXT);
CREATE TABLE IF NOT EXISTS paper_orders(order_id TEXT PRIMARY KEY,idempotency_key TEXT UNIQUE NOT NULL,account_id TEXT NOT NULL,instrument_id TEXT NOT NULL,side TEXT NOT NULL,order_type TEXT NOT NULL,quantity REAL NOT NULL,limit_price REAL,status TEXT NOT NULL,risk_result TEXT NOT NULL,fill_price REAL,fee REAL NOT NULL DEFAULT 0,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,source_quote_at TEXT,actor TEXT NOT NULL DEFAULT 'manual',ai_run_id TEXT,reason TEXT,reserved_cash REAL NOT NULL DEFAULT 0,budget_charge REAL NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS paper_fills(fill_id TEXT PRIMARY KEY,order_id TEXT NOT NULL UNIQUE REFERENCES paper_orders(order_id),instrument_id TEXT NOT NULL,side TEXT NOT NULL,quantity REAL NOT NULL,price REAL NOT NULL,fee REAL NOT NULL,currency TEXT NOT NULL,provider TEXT NOT NULL,quote_received_at TEXT NOT NULL,filled_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS paper_account_actions(owner_id TEXT NOT NULL,request_key TEXT NOT NULL,payload TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(owner_id,request_key));
CREATE TABLE IF NOT EXISTS paper_contract_overrides(owner_id TEXT NOT NULL,instrument_id TEXT NOT NULL,lot_size INTEGER NOT NULL,currency TEXT NOT NULL,source TEXT NOT NULL,source_kind TEXT NOT NULL,updated_at TEXT NOT NULL,note TEXT NOT NULL,PRIMARY KEY(owner_id,instrument_id));
CREATE TABLE IF NOT EXISTS paper_contracts(instrument_id TEXT PRIMARY KEY,lot_size INTEGER NOT NULL,currency TEXT NOT NULL,source TEXT NOT NULL,source_kind TEXT NOT NULL,updated_at TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS paper_ai_runs(run_id TEXT PRIMARY KEY,idempotency_key TEXT UNIQUE NOT NULL,account_id TEXT NOT NULL,request_json TEXT NOT NULL,status TEXT NOT NULL,answer TEXT,error TEXT,model TEXT,evidence_json TEXT NOT NULL DEFAULT '[]',created_at TEXT NOT NULL,completed_at TEXT);
CREATE INDEX IF NOT EXISTS idx_paper_orders_account ON paper_orders(account_id,status,created_at);
'''

def session(market):
    try:
        import exchange_calendars as xc
        import pandas as pd
        cal = xc.get_calendar({'CN':'XSHG','HK':'XHKG','US':'XNYS'}[market])
        return {'phase':'open' if cal.is_open_on_minute(pd.Timestamp.now(tz='UTC').floor('min'), ignore_breaks=False) else 'closed'}
    except Exception:
        return {'phase':'closed'}

def observed(q):
    try:
        d = datetime.fromisoformat(q['exchange_time'].replace('Z','+00:00'))
        return d if d.tzinfo else None
    except (ValueError, TypeError, AttributeError):
        return None

def broker(owner):
    if active_profile()['driver'] != 'sqlite':
        raise ValueError('本地模拟交易目前仅支持 SQLite 数据库。')
    with connect() as db: db.executescript(SCHEMA)
    return paper.Broker(connect, session, lambda q: {'freshness':q['freshness']}, observed, 60, owner)

def action(owner, operation, data, key=''):
    b = broker(owner)
    if operation in {'create_account','submit','reset','reset_all'} and (not key or len(key)>180):
        raise ValueError('缺少有效的请求标识')
    if operation == 'markets': return [{'market':k,**v} for k,v in paper.MARKETS.items()]
    if operation == 'accounts':
        for market in ('CN','HK','US'): b.match(market)
        with connect() as c:
            rows = c.execute("SELECT account_id FROM paper_accounts WHERE owner_id=? AND state='active' ORDER BY created_at DESC",(owner,)).fetchall()
            return [b.portfolio(c, row['account_id']) for row in rows]
    if operation == 'orders':
        for market in ('CN','HK','US'): b.match(market)
        with connect() as c:
            account = data.get('account_id') or None
            if account: b._account(c, account)
            rows = c.execute("SELECT o.* FROM paper_orders o JOIN paper_accounts a ON a.account_id=o.account_id WHERE a.owner_id=? AND a.state='active' AND (? IS NULL OR o.account_id=?) ORDER BY o.created_at DESC LIMIT ? OFFSET ?",(owner,account,account,min(100,max(1,int(data.get('limit',21)))),max(0,int(data.get('offset',0))))).fetchall()
            return [dict(row) for row in rows]
    if operation == 'create_account': return b.create_account(paper.AccountRequest.model_validate(data),key)
    if operation == 'preview': return b.preview(paper.OrderRequest.model_validate(data))
    if operation == 'submit': return b.submit(paper.OrderRequest.model_validate(data),key)
    if operation == 'cancel': return b.cancel(str(data.get('order_id','')))
    if operation in {'reset','reset_all'}:
        target = data.get('target') if operation == 'reset' else None
        return b.reset(target,paper.ResetRequest.model_validate(data['body']),key)
    if operation == 'contract':
        instrument=paper.normalize(data.get('instrument_id',''))
        with connect() as c: return b.contract(c,instrument)
    if operation == 'set_contract': return b.set_contract(data['instrument_id'],paper.ContractRequest.model_validate(data['body']))
    if operation == 'sync_hk': return asyncio.run(b.sync_hk())
    if operation == 'pull_quote':
        instrument=paper.normalize(data.get('instrument_id','')); paper.board(instrument)
        result=futu_data._run('snapshot',instrument)
        q=result.get('quote')
        if not q: raise ValueError('富途 OpenD 暂未返回该股票报价，可先使用限价挂单。')
        cols=['instrument_id','symbol','name','market','asset_class','last','currency','quote_kind','price_unit','exchange_time','received_at','provider','freshness','known_delay_seconds','change_percent','volume']
        with connect() as c:
            c.execute('INSERT INTO quotes ('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+') ON CONFLICT(instrument_id) DO UPDATE SET '+','.join(f'{k}=excluded.{k}' for k in cols[1:]),tuple(q.get(k) for k in cols))
        b.match(instrument.split(':')[0])
        return {**q,'executable':b._executable(q)}
    raise ValueError('未知模拟交易操作')
