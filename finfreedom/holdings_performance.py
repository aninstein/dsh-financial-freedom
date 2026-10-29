"""Point-in-time holdings price movement, without inventing earlier positions."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import json
from threading import RLock

from finfreedom.database import connect

ZONE = ZoneInfo('Asia/Shanghai')
_history_lock = RLock()

def record_snapshot(db, owner, currency, stamp=None):
    if not db.execute('SELECT 1 FROM personal_portfolios WHERE owner_id=? AND currency=?', (owner, currency)).fetchone():
        return
    rows = db.execute('SELECT instrument_id,quantity FROM personal_positions WHERE owner_id=? AND currency=? ORDER BY instrument_id', (owner, currency)).fetchall()
    positions = [dict(row) for row in rows]
    encoded = json.dumps(positions, ensure_ascii=False, sort_keys=True)
    latest = db.execute('SELECT positions_json FROM holdings_history WHERE owner_id=? AND currency=? ORDER BY observed_at DESC LIMIT 1', (owner, currency)).fetchone()
    if latest and json.loads(latest['positions_json']) == positions:
        return
    stamp = stamp or datetime.now(timezone.utc).isoformat(timespec='microseconds')
    db.execute('INSERT INTO holdings_history(owner_id,currency,observed_at,positions_json) VALUES(?,?,?,?)', (owner,currency,stamp,encoded))

def history(owner, currency, start, end):
    currency = str(currency or 'CNY').upper()
    if currency not in {'CNY','HKD','USD'}:
        raise ValueError('仅支持 CNY、HKD、USD')
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if last < first or (last-first).days > 62:
        raise ValueError('日期范围不得超过 63 天')
    with _history_lock, connect() as db:
        record_snapshot(db, owner, currency)
        snapshots = db.execute('SELECT observed_at,positions_json FROM holdings_history WHERE owner_id=? AND currency=? ORDER BY observed_at', (owner,currency)).fetchall()
        snapshots = [(datetime.fromisoformat(row['observed_at'].replace('Z','+00:00')).astimezone(ZONE).date(), json.loads(row['positions_json'])) for row in snapshots]
        days=[]
        day=first
        today=datetime.now(ZONE).date()
        while day <= last:
            prior=[x for x in snapshots if x[0] < day]
            changed=any(x[0] == day for x in snapshots)
            result={'date':day.isoformat(),'currency':currency,'complete':False}
            if day > today: result['reason']='future_date'
            elif not prior: result['reason']='no_holdings_history'
            elif changed: result['reason']='holdings_changed'
            else:
                positions=prior[-1][1]
                total=0.0; missing=[]; open_count=0; pending_close=False
                for item in positions:
                    instrument=item['instrument_id']; qty=item['quantity']
                    if not instrument or qty is None:
                        missing.append(instrument or '未填写代码'); continue
                    # Require the actual previous exchange session, not an arbitrary stale bar.
                    market=instrument.split(':',1)[0]
                    market={'FUND':'CN','GOLD':'CN'}.get(market,market)
                    try:
                        import exchange_calendars as xc
                        cal=xc.get_calendar({'CN':'XSHG','HK':'XHKG','US':'XNYS'}[market])
                        if not cal.is_session(day.isoformat()):
                            continue
                        open_count += 1
                        if cal.session_close(day.isoformat()).to_pydatetime() > datetime.now(timezone.utc):
                            pending_close=True; continue
                        prev=cal.previous_session(cal.date_to_session(day.isoformat())).date().isoformat()
                    except Exception:
                        missing.append(instrument); continue
                    rows=db.execute("SELECT bar_time,close,currency FROM bars WHERE instrument_id=? AND interval_name='1d' AND adjustment='none' AND (bar_time=? OR bar_time=?)", (instrument,day.isoformat(),prev)).fetchall()
                    prices={str(r['bar_time'])[:10]:r for r in rows}
                    if day.isoformat() not in prices or prev not in prices or any(prices[k]['close'] is None or prices[k]['currency'] != currency for k in (day.isoformat(),prev)):
                        missing.append(instrument); continue
                    total += float(qty)*(float(prices[day.isoformat()]['close'])-float(prices[prev]['close']))
                if not open_count and not missing: result.update(reason='non_trading_day')
                elif pending_close: result.update(reason='awaiting_close')
                elif missing: result.update(reason='missing_bars',missing_bars=missing)
                else: result.update(complete=True,day_pnl=round(total,2),method='持仓数量 × 收盘价变化估算，不含当日交易、费用和现金流')
            days.append(result);day += timedelta(days=1)
        return {'currency':currency,'days':days,'note':'根据已记录持仓和相邻交易日收盘价估算；缺少历史持仓、日线或当日持仓变动时不计算。'}
