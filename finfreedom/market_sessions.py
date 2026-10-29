"""Exchange sessions from the local calendar, without inventing holidays."""
from datetime import date, datetime, timedelta, timezone
import exchange_calendars as xc
import pandas as pd


def calendar(market, start=None, end=None):
    market = str(market or 'CN').upper()
    if market not in {'CN','HK','US'}: raise ValueError('交易日历仅支持 CN、HK、US')
    today=datetime.now(timezone.utc).date()
    try:
        first=date.fromisoformat(start) if start else today
        last=date.fromisoformat(end) if end else first+timedelta(days=30)
    except (TypeError, ValueError): raise ValueError('日期须使用 YYYY-MM-DD 格式')
    if last < first or (last-first).days > 62: raise ValueError('日期范围不得超过 63 天')
    cal=xc.get_calendar({'CN':'XSHG','HK':'XHKG','US':'XNYS'}[market])
    try:
        sessions=cal.sessions_in_range(first.isoformat(),last.isoformat())
        rows=[{'date':s.date().isoformat(),'open':cal.session_open(s).isoformat(),'close':cal.session_close(s).isoformat()} for s in sessions]
        return {'market':market,'start':str(first),'end':str(last),'sessions':rows,'source':'exchange_calendars 本地交易日历','state':'available'}
    except Exception:
        return {'market':market,'start':str(first),'end':str(last),'sessions':[],'source':'exchange_calendars 本地交易日历','state':'unavailable','data_gap':'本地日历不覆盖所选日期，请更新交易所日历。'}


def status(market):
    market=str(market or 'CN').upper()
    if market not in {'CN','HK','US'}: raise ValueError('交易状态仅支持 CN、HK、US')
    now=pd.Timestamp.now(tz='UTC').floor('min')
    cal=xc.get_calendar({'CN':'XSHG','HK':'XHKG','US':'XNYS'}[market])
    try:
        phase='open' if cal.is_open_on_minute(now,ignore_breaks=False) else 'closed'
        return {'market':market,'phase':phase,'as_of':now.isoformat(),'source':'exchange_calendars 本地交易日历','note':'按交易日历计算；实际交易所临时停市以交易所公告为准。'}
    except Exception:
        return {'market':market,'phase':'unknown','as_of':now.isoformat(),'source':'exchange_calendars 本地交易日历','data_gap':'日历未覆盖当前日期。'}
