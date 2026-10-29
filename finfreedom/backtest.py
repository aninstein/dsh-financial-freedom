"""Original Financial Freedom SMA backtest, adapted to the local DSH database."""
from datetime import date, datetime, timezone
import json, math, re, uuid
from finfreedom.database import connect


def run(owner, data):
    instrument=str(data.get('instrument_id','')).upper().strip()
    if not re.fullmatch(r'(CN|HK|US|FUND|GOLD):[A-Z0-9._-]{1,48}',instrument): raise ValueError('标的代码无效')
    start=date.fromisoformat(str(data.get('start',''))); end=date.fromisoformat(str(data.get('end','')))
    fast=int(data.get('fast_window',20)); slow=int(data.get('slow_window',50)); fee=float(data.get('fee_bps',10)); slippage=float(data.get('slippage_bps',5))
    if end <= start or end > date.today(): raise ValueError('回测日期必须为有效历史区间')
    if not (2 <= fast <= 250 and 3 <= slow <= 500 and fast < slow and 0 <= fee <= 1000 and 0 <= slippage <= 1000): raise ValueError('策略参数无效')
    with connect() as db:
        rows=db.execute("SELECT bar_time,close FROM bars WHERE instrument_id=? AND interval_name='1d' AND adjustment='none' AND bar_time>=? AND bar_time<=? ORDER BY bar_time",(instrument,start.isoformat(),end.isoformat())).fetchall()
        manifest=db.execute("SELECT dataset_version FROM dataset_manifests WHERE instrument_id=? AND interval_name='1d' ORDER BY ingested_at DESC LIMIT 1",(instrument,)).fetchone()
    if len(rows)<slow+2: raise ValueError(f'本地日线不足，至少需要 {slow+2} 条，当前 {len(rows)} 条')
    closes=[float(x['close']) for x in rows]
    if any(not math.isfinite(x) or x<=0 for x in closes): raise ValueError('日线包含无效收盘价')
    signals=[0 if i+1<slow else int(sum(closes[i-fast+1:i+1])/fast>sum(closes[i-slow+1:i+1])/slow) for i in range(len(closes))]
    daily=[]; position=0; cost=(fee+slippage)/10000
    for i in range(1,len(closes)):
        new=signals[i-1]; daily.append(new*(closes[i]/closes[i-1]-1)-abs(new-position)*cost); position=new
    equity=peak=1.; drawdown=0.
    for value in daily:
        equity*=1+value; peak=max(peak,equity); drawdown=min(drawdown,equity/peak-1)
    mean=sum(daily)/len(daily); variance=sum((x-mean)**2 for x in daily)/max(1,len(daily)-1)
    metrics={'total_return':equity-1,'benchmark_buy_hold_return':closes[-1]/closes[0]-1,'max_drawdown':drawdown,'annualized_volatility':variance**.5*252**.5,'sharpe_ratio':mean*252**.5/variance**.5 if variance>0 else None,'observations':len(daily),'ending_position':position,'label':'historical research; not a forecast'}
    params={'fast_window':fast,'slow_window':slow,'fee_bps':fee,'slippage_bps':slippage,'signal':'close SMA crossover; position applied next bar','adjustment':'none'}
    run={'run_id':'R-'+uuid.uuid4().hex[:12],'strategy_id':'sma-trend','strategy_version':'1.0.0','instrument_id':instrument,'dataset_version':manifest['dataset_version'] if manifest else 'unversioned-cache','parameters':params,'metrics':metrics,'start':rows[0]['bar_time'],'end':rows[-1]['bar_time'],'created_at':datetime.now(timezone.utc).isoformat()}
    with connect() as db:
        db.execute('INSERT INTO research_runs(run_id,owner_id,strategy_id,strategy_version,instrument_id,dataset_version,parameters,metrics,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(run['run_id'],owner,run['strategy_id'],run['strategy_version'],instrument,run['dataset_version'],json.dumps(params),json.dumps(metrics),run['created_at']))
    return run
