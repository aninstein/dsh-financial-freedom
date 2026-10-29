"""Bounded, read-only OpenD requests in a subprocess (SDK logs never reach MCP stdout)."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import numbers
import os
import re
import sys
from datetime import datetime, timezone

from finfreedom.providers.futu_provider import INDEX_CODES, INDEX_NAMES, address, normalize_snapshot


def _identifier(code: str, stock_type: str = '') -> str | None:
    prefix, dot, symbol = code.upper().partition('.')
    if not dot or not re.fullmatch(r'[A-Z0-9._-]{1,24}', symbol):
        return None
    if prefix in {'SH', 'SZ'}:
        market = 'FUND' if 'ETF' in stock_type.upper() else 'CN'
    elif prefix in {'HK', 'US'}:
        market = prefix
    else:
        return None
    return f'{market}:{symbol}'


def quotes() -> dict:
    from futu import OpenQuoteContext, RET_OK
    host, port = address()
    ctx = OpenQuoteContext(host=host, port=port)
    try:
        state, _ = ctx.get_global_state()
        if state != RET_OK:
            raise RuntimeError('OpenD 未连接')
        result, groups = ctx.get_user_security_group()
        if result != RET_OK:
            raise RuntimeError('无法读取富途自选分组')
        entries = {}
        failures = 0
        for group in groups.to_dict(orient='records')[:8]:
            name = str(group.get('group_name') or '')[:80]
            if not name:
                continue
            status, frame = ctx.get_user_security(name)
            if status != RET_OK:
                failures += 1
                continue
            for item in frame.to_dict(orient='records'):
                code = str(item.get('code') or '').upper()
                instrument_id = _identifier(code, str(item.get('stock_type') or ''))
                if not instrument_id:
                    continue
                if code not in entries:
                    if len(entries) >= 200:
                        continue
                    entries[code] = {'instrument_id':instrument_id, 'code':code,
                                     'name':str(item.get('name') or '')[:120], 'groups':[]}
                if name not in entries[code]['groups']:
                    entries[code]['groups'].append(name)
        codes = list(entries)
        quoted = {}
        for offset in range(0, len(codes), 50):
            status, frame = ctx.get_market_snapshot(codes[offset:offset + 50])
            if status != RET_OK:
                failures += 1
                continue
            for item in frame.to_dict(orient='records'):
                code = str(item.get('code') or '').upper()
                row = entries.get(code)
                if not row:
                    continue
                normalized = normalize_snapshot(item, row['instrument_id'])
                if normalized and normalized[0] == 'quote':
                    quote = normalized[1]
                    quote['freshness'] = 'unknown'
                    quoted[code] = quote
        rows = []
        for code, entry in entries.items():
            quote = quoted.get(code, {})
            rows.append({**entry, **quote, 'name':quote.get('name') or entry['name'],
                         'source':'富途 OpenD', 'quote_available':bool(quote)})
        indices = []
        for offset in range(0, len(INDEX_CODES), 2):
            index_codes = list(INDEX_CODES)[offset:offset + 2]
            status, frame = ctx.get_market_snapshot(index_codes)
            if status != RET_OK:
                failures += 1
                continue
            for item in frame.to_dict(orient='records'):
                normalized = normalize_snapshot(item)
                if normalized and normalized[0] == 'index':
                    indices.append({**normalized[1], 'name':INDEX_NAMES.get(normalized[1]['id'], normalized[1]['id']),
                                    'market':'HK' if str(item.get('code')).startswith('HK.') else 'CN',
                                    'freshness':'unknown'})
        return {'state':'partial' if failures or len(groups) > 8 else 'connected', 'source':'富途 OpenD',
                'as_of':datetime.now(timezone.utc).isoformat(), 'group_count':len(groups),
                'rows':rows, 'indices':indices, 'quote_count':len(quoted), 'failed_requests':failures,
                'note':'为遵守 OpenD 频率限制，目前读取前 8 个自选分组、最多 200 个标的；快照时效以来源时间和行情权限为准。'}
    finally:
        ctx.close()


def accounts(mode: str, summary: bool = False, discover: bool = False) -> dict:
    from futu import OpenSecTradeContext, RET_OK
    if mode not in {'SIMULATE', 'REAL'}:
        raise ValueError('未知账户环境')
    allowed = {x.strip() for x in os.getenv('FINFREEDOM_FUTU_REAL_ACCOUNT_IDS', '').split(',') if x.strip()}
    tokens = {x.strip() for x in os.getenv('FINFREEDOM_FUTU_REAL_ACCOUNT_TOKENS', '').split(',') if x.strip()}
    host, port = address()
    found, errors = [], []
    for market in (('HK','US','CN') if mode == 'SIMULATE' else ('HK','US')):
        ctx = OpenSecTradeContext(filter_trdmarket=market, host=host, port=port, security_firm='FUTUSECURITIES')
        try:
            status, frame = ctx.get_acc_list()
            if status != RET_OK:
                errors.append(market)
                continue
            for item in frame.to_dict(orient='records'):
                account = str(item.get('acc_id') or '')
                if not account or str(item.get('trd_env')).upper() != mode:
                    continue
                auth = item.get('trdmarket_auth')
                if auth and market not in re.findall(r'[A-Z]+', str(auth).upper()):
                    continue
                ident = hashlib.sha256(f'FUTUSECURITIES:{mode}:{market}:{account}'.encode()).hexdigest()[:24]
                identifier = f'futu-{mode.lower()}-{market.lower()}-{ident}'
                authorized = mode != 'REAL' or account in allowed or identifier in tokens
                if not authorized and not discover: continue
                if any(row['id'] == identifier for row in found):
                    continue
                currency = {'HK':'HKD','US':'USD','CN':'CNH'}[market]
                if summary:
                    found.append({'id':identifier, 'market':market, 'mode':mode, 'currency':currency,
                                  'account_suffix':account[-4:], 'authorized':authorized, 'managed_by_env':mode == 'REAL' and account in allowed, 'state':'summary',
                                  'as_of':datetime.now(timezone.utc).isoformat()})
                    continue
                kwargs = {'trd_env':mode, 'acc_id':int(account), 'refresh_cache':True, 'currency':currency}
                funds_status, funds = ctx.accinfo_query(**kwargs)
                positions_status, positions = ctx.position_list_query(**kwargs)
                fund_rows = funds.to_dict(orient='records') if funds_status == RET_OK else []
                position_rows = positions.to_dict(orient='records') if positions_status == RET_OK else []
                f = fund_rows[0] if len(fund_rows) == 1 else {}
                found.append({'id':identifier, 'market':market, 'mode':mode, 'currency':currency,
                              'account_suffix':account[-4:], 'cash':f.get('cash'), 'equity':f.get('total_assets'),
                              'positions':[{'instrument_id':_identifier(str(p.get('code') or '')),
                                            'name':str(p.get('stock_name') or ''), 'quantity':p.get('qty'),
                                            'sellable':p.get('can_sell_qty'), 'average_cost':p.get('cost_price'),
                                            'market_value':p.get('market_val')} for p in position_rows],
                              'state':'connected' if funds_status == RET_OK and positions_status == RET_OK else 'partial',
                              'as_of':datetime.now(timezone.utc).isoformat()})
        finally:
            ctx.close()
    return {'accounts':found, 'source':'富途 OpenD', 'mode':mode, 'state':'partial' if errors else 'connected',
            'note':'实盘账户按配置白名单读取；仅展示账户资金和持仓，不执行交易。', 'failed_markets':errors}


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, numbers.Real):
        return value.item() if math.isfinite(float(value)) and hasattr(value, 'item') else (value if math.isfinite(float(value)) else None)
    return value


def snapshot(instrument: str) -> dict:
    from futu import OpenQuoteContext, RET_OK
    from finfreedom.providers.futu_provider import code_for
    code = code_for(instrument)
    if not code: return {'state':'unavailable'}
    host, port = address()
    ctx = OpenQuoteContext(host=host, port=port)
    try:
        status, frame = ctx.get_market_snapshot([code])
        if status != RET_OK or frame.empty: return {'state':'unavailable'}
        row = normalize_snapshot(frame.to_dict(orient='records')[0], instrument)
        return {'state':'connected', 'quote':row[1]} if row and row[0] == 'quote' else {'state':'unavailable'}
    finally:
        ctx.close()


def main() -> None:
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            data = quotes() if sys.argv[1] == 'quotes' else snapshot(sys.argv[2]) if sys.argv[1] == 'snapshot' else accounts(sys.argv[2], summary=sys.argv[1] in {'account_summary','discover_real'}, discover=sys.argv[1] == 'discover_real')
        print(json.dumps(_json_safe(data), ensure_ascii=False, default=str, allow_nan=False))
    except Exception as exc:
        print(json.dumps({'state':'unavailable', 'source':'富途 OpenD', 'error':type(exc).__name__, 'rows':[]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
