"""Read imported public-market caches without pretending they are live."""
import json
import math
from collections import Counter
from contextlib import contextmanager
from finfreedom.database import connect
from finfreedom.cycle_analysis import analyze


def cached(key):
    with connect() as db:
        row = db.execute('SELECT payload,updated_at,last_error FROM workspace_cache WHERE cache_key=?', (key,)).fetchone()
    if not row or not row['payload']:
        return None
    value = json.loads(row['payload'])
    value.update(state='stale', freshness='stale', updated_at=row['updated_at'], cache_expired=True)
    value['error'] = '历史缓存，尚未接入自动更新；请核对来源时间。'
    return value


def news(query='', limit=30):
    with connect() as db:
        rows = db.execute("SELECT * FROM research_news WHERE (?='' OR title LIKE ? OR content LIKE ? OR associations_json LIKE ?) ORDER BY published_at DESC,first_seen_at DESC LIMIT ?", (query, *[f'%{query}%']*3, min(100,max(1,int(limit))))).fetchall()
    sources = [cached('research:news_cls:ALL'), cached('research:news_em:ALL')]
    return {'rows':[{**dict(r), 'matched_sectors':json.loads(r['associations_json'])} for r in rows], 'sources':[s for s in sources if s], 'state':'stale', 'note':'历史缓存，尚未接入自动更新。'}


def funds(query='', category='all', page=1):
    d = cached('funds:catalog')
    if not d: raise ValueError('基金目录缓存不可用')
    rows = d['rows']; categories = dict(sorted(Counter(tag for x in rows for tag in x.get('tags', [x.get('category')]) if tag).items()))
    needle = query.casefold().strip()
    if needle: rows = [x for x in rows if any(needle in str(x.get(k,'')).casefold() for k in ('code','name','pinyin'))]
    if category != 'all': rows = [x for x in rows if category in x.get('tags',[x.get('category')])]
    total=len(rows); page=max(1,min(int(page),max(1,math.ceil(total/20))))
    return {**{k:d.get(k) for k in ('state','error','updated_at','source','source_url')}, 'rows':rows[(page-1)*20:page*20], 'total':total,'page':page,'page_size':20,'categories':categories, 'coverage_note':'历史目录缓存，基金状态以来源和交易平台为准。'}


def rotation():
    windows=['今日','5日','10日']; datasets=[cached('research:rotation:'+w) or {'rows':[], 'state':'unavailable'} for w in windows]
    maps={w:{r['名称']:r for r in data.get('rows',[]) if r.get('名称')} for w,data in zip(windows,datasets)}
    names=set().union(*(set(m) for m in maps.values()))
    common={n for n in names if all(isinstance(maps[w].get(n,{}).get(w+'涨跌幅'),(int,float)) for w in windows)}
    ranks={w:{n:i+1 for i,n in enumerate(sorted(common,key=lambda n:(-float(maps[w][n][w+'涨跌幅']),n)))} for w in windows}
    rows=[]; threshold=max(3,math.ceil(len(common)*.15))
    for name in names:
        item={'name':name,'complete':name in common,'windows':{},'previous_capture_rank_change':None}
        for w in windows:
            raw=maps[w].get(name,{})
            item['windows'][w]={'return_percent':raw.get(w+'涨跌幅'),'main_net_yuan':raw.get(w+'主力净流入-净额'),'fund_net_yuan':raw.get('资金净额-元'),'main_net_ratio_percent':raw.get(w+'主力净流入-净占比'),'rank':ranks[w].get(name)}
        r1,r5,r10=(ranks[w].get(name) for w in windows)
        item['rank_improvement']=r5-r1 if item['complete'] else None
        item['phase']='insufficient' if not item['complete'] else ('improving' if r5-r1>=threshold else 'weakening' if r1-r5>=threshold else 'persistent_leader' if max(r1,r5,r10)<=max(1,math.ceil(len(common)*.3)) else 'mixed')
        rows.append(item)
    rows.sort(key=lambda r:(not r['complete'],r['windows']['今日']['rank'] or 9999,r['name']))
    return {'rows':rows,'common_universe':len(common),'state':'stale','sources':datasets,'history':[],'method':'仅对三期均有收益的共同板块按收益降序排名，5日排名减今日排名为跨窗口改善。','note':'历史缓存；同花顺行业资金净额不等同主力净流入，跨窗口不代表跨日变化。'}


def flows():
    data=cached('research:market_flow:CN') or {'rows':[],'state':'unavailable'}
    data['northbound']=cached('flows:northbound') or {'rows':[],'state':'unavailable','note':'北向资金缓存不可用。'}
    rot=cached('research:rotation:今日') or {'rows':[]}
    rows=[{'name':x.get('名称'),'change_percent':x.get('今日涨跌幅'),'net_flow_yuan':x.get('资金净额-元'),'main_net_ratio_percent':None} for x in rot.get('rows',[]) if x.get('资金净额-元') is not None]
    rows.sort(key=lambda x:x['net_flow_yuan'],reverse=True)
    data['sectors']={'rows':rows[:30],'state':'stale','source':rot.get('source'),'received_at':rot.get('received_at'),'flow_metric':'行业资金净额','note':'同花顺行业资金净额，非主力净流入；历史缓存。'}
    data['coverage']={'market':'沪深大盘成交分类资金估计','stock':'个股资金页','sector':'同花顺行业资金净额','northbound':'历史北向数据'}
    return data


def index_detail(identifier):
    d=cached('research:index:'+identifier)
    if not d: raise ValueError('指数历史缓存不可用')
    rows=d.get('rows',[])
    class DB:
        def execute(self,sql,params):
            self.start, self.end = params[1], params[2]
            return self
        def fetchall(self): return [{**x,'provider':d.get('source'),'received_at':d.get('received_at')} for x in rows if self.start <= x['bar_time'] < self.end]
    @contextmanager
    def memory(): yield DB()
    analysis=analyze(memory,identifier)
    return {**d,'instrument_id':identifier,'bars':rows,'bars_source':d.get('source'),'analysis':analysis,'index':True,
            'daily_metrics':{'sma_20':analysis['moving_averages']['20'],'sma_50':None,'return_over_window':analysis['sample_return'], 'annualized_volatility_20d':analysis['annualized_volatility_20d'],'max_drawdown_in_window':analysis['max_drawdown'],'first_bar':analysis['first_bar'],'last_bar':analysis['last_bar'],'observations':analysis['observations']}}


def instrument(identifier):
    with connect() as db:
        quote = db.execute('SELECT * FROM quotes WHERE instrument_id=?',(identifier,)).fetchone()
        bars = db.execute("SELECT * FROM bars WHERE instrument_id=? AND interval_name='1d' AND adjustment='none' ORDER BY bar_time DESC LIMIT 500",(identifier,)).fetchall()
        watched = db.execute('SELECT 1 FROM watchlist WHERE instrument_id=?',(identifier,)).fetchone()
    a=analyze(connect,identifier); q=dict(quote) if quote else None
    return {'instrument_id':identifier,'name':q['name'] if q else identifier,'quote':q,'watched':bool(watched),'bars':list(reversed([dict(b) for b in bars])),'bars_source':q.get('provider') if q else None,'daily_metrics':{'sma_20':a['moving_averages']['20'],'sma_50':None,'return_over_window':a['sample_return'],'annualized_volatility_20d':a['annualized_volatility_20d'],'max_drawdown_in_window':a['max_drawdown'],'first_bar':a['first_bar'],'last_bar':a['last_bar'],'observations':a['observations']}}


def dossier(identifier, sections):
    valid={'profile','snapshot','financials','ownership','dividends','flow','news','announcements','income','balance','cashflow','holders','business','reports'}
    result={}
    for name in sections:
        if name not in valid: continue
        item=cached(f'dossier:{identifier}:{name}') or {'rows':[],'state':'unavailable','source':'本机缓存','error':'该资料尚未采集。'}
        item['section']=name; result[name]=item
    return {'sections':result,'links':[]}
