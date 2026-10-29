// Adapter from the original page contracts to the DSH read-only plugin API.
async function read(resource, query, signal) {
  const params = new URLSearchParams({resource});
  for (const key of ['currency', 'market', 'instrument_id', 'connection_id', 'start', 'end', 'limit', 'offset', 'page', 'category', 'code', 'name', 'sections', 'path', 'refresh', 'date']) {
    if (query.get(key)) params.set(key, query.get(key));
  }
  if (query.get('q')) params.set('query', query.get('q'));
  const response = await fetch('/finfreedom/api/read?' + params, {headers:{'X-Finfreedom-Client':'1'}, signal});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || '数据暂不可用');
  return result.data;
}
export async function dshRequest(path, {method='GET', signal, body, headers={}}={}) {
  const paperUrl = new URL(path, 'http://workspace.local');
  const pp = paperUrl.pathname;
  let operation, data = body || {};
  if (method === 'GET' && pp === '/accounts') operation='accounts';
  else if (method === 'GET' && pp === '/paper/markets') operation='markets';
  else if (method === 'GET' && pp === '/paper/ai/runs') return [];
  else if (method === 'GET' && pp === '/paper/orders') {operation='orders'; data=Object.fromEntries(paperUrl.searchParams);}
  else if (method === 'GET' && /^\/paper\/contracts\/[^/]+$/.test(pp)) {operation='contract'; data={instrument_id:decodeURIComponent(pp.split('/').at(-1))};}
  else if (method === 'POST' && pp === '/paper/accounts') operation='create_account';
  else if (method === 'POST' && pp === '/paper/orders/preview') operation='preview';
  else if (method === 'POST' && pp === '/paper/orders') operation='submit';
  else if (method === 'POST' && /^\/paper\/orders\/[^/]+\/cancel$/.test(pp)) {operation='cancel'; data={order_id:decodeURIComponent(pp.split('/')[3])};}
  else if (method === 'POST' && pp === '/paper/accounts/reset-all') {operation='reset_all'; data={body};}
  else if (method === 'POST' && /^\/paper\/accounts\/[^/]+\/reset$/.test(pp)) {operation='reset'; data={target:decodeURIComponent(pp.split('/')[3]),body};}
  else if (method === 'POST' && pp === '/paper/quotes/pull') operation='pull_quote';
  else if (method === 'POST' && pp === '/paper/contracts/sync-hk') operation='sync_hk';
  else if (method === 'PUT' && /^\/paper\/contracts\/[^/]+$/.test(pp)) {operation='set_contract'; data={instrument_id:decodeURIComponent(pp.split('/').at(-1)),body};}
  if (operation) {
    const res=await fetch('/finfreedom/api/paper',{method:'POST',headers:{'X-Finfreedom-Client':'1','Content-Type':'application/json'},body:JSON.stringify({operation,data,key:headers['Idempotency-Key'] || ''}),signal});
    const result=await res.json(); if (!res.ok) throw new Error(result.error || '模拟交易暂不可用'); return result.data;
  }
  if (method === 'PUT' && path === '/live/read-access') {
    const res=await fetch('/finfreedom/api/futu-read-access',{method:'PUT',headers:{'X-Finfreedom-Client':'1','Content-Type':'application/json'},body:JSON.stringify(body),signal});
    const result=await res.json(); if (!res.ok) throw new Error(result.error || '保存账户权限失败'); return result.data;
  }
  if (method === 'PUT' && ['/workspace/cards','/workspace/calendar-state'].includes(path)) {
    const resource = path.endsWith('cards') ? 'cards' : 'calendar';
    const res=await fetch('/finfreedom/api/workspace-state',{method:'PUT',headers:{'X-Finfreedom-Client':'1','Content-Type':'application/json'},body:JSON.stringify({resource,...body}),signal});
    const value=await res.json(); if(!res.ok) throw new Error(value.error || '保存失败'); return value.data;
  }
  if (method === 'PUT' && /^\/holdings\/(CNY|HKD|USD)$/.test(path)) {
    const res = await fetch('/finfreedom/api/holdings', {method:'PUT', headers:{'X-Finfreedom-Client':'1','Content-Type':'application/json'}, body:JSON.stringify({currency:path.split('/').at(-1), snapshot:body}), signal});
    const data = await res.json(); if (!res.ok) throw new Error(data.error || '保存失败'); return data.data;
  }
  if ((method === 'PUT' && path === '/ai/memory/wiki/file') || (method === 'DELETE' && path.startsWith('/ai/memory/entries/'))) {
    const payload = method === 'PUT' ? {action:'save', ...body} : {action:'delete',entry_id:decodeURIComponent(path.split('/').at(-1))};
    const res=await fetch('/finfreedom/api/memory-edit',{method:'POST',headers:{'X-Finfreedom-Client':'1','Content-Type':'application/json'},body:JSON.stringify(payload),signal});
    const value=await res.json(); if (!res.ok) throw new Error(value.error || '操作失败'); return value.data;
  }
  if (method === 'POST' && path === '/research/backtests') {
    const res=await fetch('/finfreedom/api/backtest',{method:'POST',headers:{'X-Finfreedom-Client':'1','Content-Type':'application/json'},body:JSON.stringify(body),signal});
    const value=await res.json(); if(!res.ok) throw new Error(value.error || '回测失败'); return value.data;
  }
  if (method !== 'GET') throw new Error('此操作尚未接入 DSH 工作台；数据没有被修改。');
  const url = new URL(path, 'http://workspace.local');
  const q = url.searchParams;
  if (url.pathname === '/holdings/performance/history') return read('holdings_performance',q,signal);
  if (url.pathname === '/calendar/insights') return read('calendar_insights',q,signal);
  if (url.pathname === '/markets/calendar') {
    const markets = (q.get('markets') || 'CN,HK,US').split(',');
    const results = await Promise.all(markets.map(market => { const p = new URLSearchParams(q); p.set('market',market); return read('market_calendar',p,signal); }));
    if (results.some(x => x.state !== 'available')) throw new Error('本地交易所日历未覆盖所选日期');
    const days=[]; const start=new Date(q.get('start')+'T12:00:00'), end=new Date(q.get('end')+'T12:00:00');
    for (let d=start; d<=end; d.setDate(d.getDate()+1)) { const key=[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-'); const row={date:key}; results.forEach((result,i)=>{ const session=result.sessions.find(s=>s.date===key); const zone={CN:'Asia/Shanghai',HK:'Asia/Hong_Kong',US:'America/New_York'}[markets[i]]; const fmt=x=>new Intl.DateTimeFormat('zh-CN',{timeZone:zone,hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).format(new Date(x)); row[markets[i]]=session?{is_open:true,open:fmt(session.open),close:fmt(session.close)}:{is_open:false}; }); days.push(row); }
    return {days};
  }
  if (url.pathname === '/ai/memory/wiki/tree') return read('wiki_tree',q,signal);
  if (url.pathname === '/ai/memory/wiki/file') return read('wiki_file',q,signal);
  if (url.pathname === '/ai/memory/settings') return read('memory_settings',q,signal);
  if (url.pathname === '/holdings') {
    const portfolios = await read('holdings',q,signal);
    for (const p of portfolios) {
      p.allocation = {stock:0, fund:0, gold:0};
      for (const x of p.positions) {
        x.valuation_source = x.valuation_source === '行情' ? 'quote' : x.valuation_source === '手动' ? 'manual' : 'missing';
        x.unrealized_pnl = x.current_value != null && x.cost_basis != null ? x.current_value-x.cost_basis : null;
        x.unrealized_return_pct = x.unrealized_pnl != null && x.cost_basis ? x.unrealized_pnl / x.cost_basis * 100 : null;
        if (x.current_value != null && p.allocation[x.asset_class] != null) p.allocation[x.asset_class] += x.current_value;
        if (x.freshness === 'stale') x.provider = (x.provider || '缓存行情') + ' · 历史缓存';
      }
      const costs = p.positions.map(x => x.cost_basis);
      p.holdings_cost = costs.every(x => x != null) ? costs.reduce((a,b) => a+b, 0) : null;
      p.holdings_pnl = p.holdings_cost != null && p.holdings_value != null ? p.holdings_value-p.holdings_cost : null;
      p.holdings_return_pct = p.holdings_pnl != null && p.holdings_cost ? p.holdings_pnl/p.holdings_cost*100 : null;
      p.total_pnl = p.total_assets != null && p.principal != null ? p.total_assets-p.principal : null;
      p.total_return_pct = p.total_pnl != null && p.principal ? p.total_pnl/p.principal*100 : null;
    }
    return {currencies:['CNY','HKD','USD'], portfolios};
  }
  if (url.pathname === '/watchlist') return (await read('watchlist',q,signal)).rows;
  if (url.pathname === '/quotes') {
    q.set('limit', '20'); const d = await read('quotes',q,signal);
    return {quotes:d.rows, count:d.rows.length, total_count:d.total_count};
  }
  if (url.pathname === '/instruments/search') return {instruments:(await read('instrument_search',q,signal)).matches};
  if (q.get('refresh') === 'true') throw new Error('当前显示导入的历史缓存，自动采集尚未接入。');
  if (url.pathname === '/research/news') { if (q.get('query')) q.set('q',q.get('query')); return read('news',q,signal); }
  if (url.pathname === '/research/liquidity') return read('liquidity',q,signal);
  if (url.pathname === '/research/flows') return read('flows',q,signal);
  if (url.pathname === '/research/rotation') return read('rotation',q,signal);
  if (url.pathname === '/research/funds') return read('funds',q,signal);
  if (/^\/research\/funds\/\d{6}$/.test(url.pathname)) {q.set('code',url.pathname.split('/').at(-1)); return read('fund_detail',q,signal);}
  if (url.pathname === '/workspace/sectors') return read('sectors',q,signal);
  if (url.pathname.startsWith('/workspace/instruments/')) {
    const parts = url.pathname.split('/'); q.set('instrument_id',decodeURIComponent(parts[3]));
    return read(parts[4] === 'dossier' ? 'dossier' : 'instrument',q,signal);
  }
  if (url.pathname === '/research/cycles') return read('cycles',q,signal);
  if (url.pathname.startsWith('/workspace/indices/') && url.pathname !== '/workspace/indices/live') {q.set('instrument_id',decodeURIComponent(url.pathname.split('/').at(-1))); return read('index_detail',q,signal);}
  if (url.pathname === '/providers/futu/status') {
    const d=await read('providers',q,signal), p=d.rows?.[0];
    return {enabled:true, connected:d.state === 'connected' || d.state === 'partial', opend_reachable:!!p?.opend_reachable, opend_port:p?.opend_port, last_quote_count:p?.quote_count, last_success:p?.received_at, last_error:p?.note};
  }
  if (url.pathname === '/providers') return (await read('providers',q,signal)).rows;
  if (url.pathname === '/workspace/indices') return (await read('indices',q,signal)).rows;
  if (url.pathname === '/workspace/indices/live') { const d=await read('index_live',q,signal); return {indices:d.rows, provider:'futu', served_at:d.as_of}; }
  if (url.pathname === '/live/status') return read('live_futu_summary',q,signal);
  if (url.pathname.startsWith('/live/accounts/')) {
    q.set('connection_id',decodeURIComponent(url.pathname.split('/').at(-1)));
    return read('live_futu_accounts',q,signal);
  }
  if (url.pathname === '/futu-paper/status') {
    const d = await read('paper_futu_summary',q,signal);
    return {enabled:false, note:(d.state === 'unavailable' || d.state === 'disabled' ? '暂时无法读取富途 OpenD 模拟账户，请检查连接后刷新。' : d.state === 'partial' ? '部分市场的模拟账户读取失败，可稍后刷新。' : '账户列表来自 OpenD；资金与持仓可按需查询。模拟委托尚未接入 DSH。'), connections:(d.accounts || []).map(a => ({...a, label:`${a.market} 模拟账户 · 尾号 ${a.account_suffix}`, trading_enabled:false}))};
  }
  if (url.pathname.startsWith('/futu-paper/accounts/')) {
    q.set('connection_id', decodeURIComponent(url.pathname.split('/').at(-1)));
    return read('paper_futu_accounts',q,signal);
  }
  if (url.pathname === '/research/backtests') return await read('backtests',q,signal);
  if (url.pathname === '/ai/research') return await read('research',q,signal);
  if (url.pathname === '/ai/documents') return await read('documents',q,signal);
  if (url.pathname === '/markets/status') return {markets:[]};
  if (url.pathname === '/accounts' || url.pathname === '/ai/sessions') return [];
  if (url.pathname === '/ai/status') return {enabled:false, supports_vision:false};
  if (url.pathname === '/workspace/cards') return read('cards',q,signal);
  if (url.pathname === '/workspace/calendar-state') return read('calendar',q,signal);
  throw new Error('此页面的数据或操作尚未接入 DSH。');
}
