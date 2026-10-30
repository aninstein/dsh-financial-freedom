window.__ModuleLoader__.load({
  id: '@finfreedom/dsh-plugin',
  factory: (require) => {
    const React = require('react');
    const ReactDOM = require('react-dom');
    const h = React.createElement;
    // Paths adapted from Financial Freedom's shared icon set.
    const iconPaths = {
      wallet:'M3 6h16v14H3zM3 6V4h14M15 11h6v5h-6z',
      star:'m12 3 2.8 5.7 6.2.9-4.5 4.4 1.1 6.2-5.6-3-5.6 3 1.1-6.2L3 9.6l6.2-.9L12 3Z',
      globe:'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20',
      researchChat:'M4 4h16v12H9l-5 4V4ZM9 10h6M12 7v6',
      grid:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
      calendar:'M8 2v4M16 2v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2ZM7 14h3M14 14h3M7 18h3',
      candles:'M5 3v18M3 7h4v6H3zM12 2v20M10 11h4v7h-4zM19 4v16M17 6h4v5h-4z',
      bank:'m3 10 9-7 9 7M5 10h14M6 10v9M10 10v9M14 10v9M18 10v9M4 21h16M3 19h18',
      coins:'M12 4c-4.4 0-8 1.6-8 3.5S7.6 11 12 11s8-1.6 8-3.5S16.4 4 12 4ZM4 8v4c0 1.9 3.6 3.5 8 3.5M4 12v4c0 1.9 3.6 3.5 8 3.5M20 12.5c0-1.7-2.5-3-5.5-3S9 10.8 9 12.5s2.5 3 5.5 3 5.5-1.3 5.5-3ZM9 12.5v4c0 1.7 2.5 3 5.5 3s5.5-1.3 5.5-3v-4',
      layers:'m12 3 10 5-10 5L2 8l10-5ZM2 12l10 5 10-5M2 16l10 5 10-5',
      fund:'M12 3a9 9 0 1 0 9 9h-9V3ZM15 3.5A8.5 8.5 0 0 1 20.5 9H15V3.5Z',
      rotation:'M20 7a8 8 0 0 0-13-2L4 8M4 4v4h4M4 17a8 8 0 0 0 13 2l3-3M20 20v-4h-4',
      flask:'M9 3h6M10 3v6L4 19a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2L14 9V3M8 14h8',
      file:'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6ZM14 2v6h6M8 13h8M8 17h6',
      settings:'M10 2.6h4l.6 2.3c.6.2 1.2.4 1.7.8l2.1-1.1 2.8 2.8-1.1 2.1c.3.5.6 1.1.8 1.7l2.3.6v4l-2.3.6a8 8 0 0 1-.8 1.7l1.1 2.1-2.8 2.8-2.1-1.1a8 8 0 0 1-1.7.8l-.6 2.3h-4l-.6-2.3a8 8 0 0 1-1.7-.8l-2.1 1.1-2.8-2.8 1.1-2.1a8 8 0 0 1-.8-1.7l-2.3-.6v-4l2.3-.6c.2-.6.4-1.2.8-1.7L4.6 7.4l2.8-2.8 2.1 1.1c.5-.3 1.1-.6 1.7-.8L10 2.6ZM12 9a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z'
    };
    const pageIcons = {guide:'researchChat',holdings:'wallet',watchlist:'star',markets:'globe',calendar:'calendar',indices:'candles',news:'file',liquidity:'bank',flows:'wallet',funds:'fund',sectors:'rotation',gold:'coins',research:'flask',backtests:'flask',documents:'file',paper:'wallet','futu-paper':'wallet',live:'wallet',wiki:'file',settings:'settings'};
    function Icon({name}) {
      return h('svg', {className:'finfreedom-nav-icon', viewBox:'0 0 24 24', width:18, height:18,
        fill:'none', stroke:'currentColor', strokeWidth:1.6, strokeLinecap:'round', strokeLinejoin:'round', 'aria-hidden':true},
        h('path', {d:iconPaths[name] || iconPaths.grid}));
    }
    const pages = [
      {id:'guide', title:'AI投研', description:'从常用投资研究场景开始。'},
      {id:'holdings', title:'我的持仓', icon:'◫', resource:'holdings', description:'查看各币种的持仓和现金。'},
      {id:'watchlist', title:'我的自选', icon:'☆', resource:'watchlist', description:'查看关注的标的与最近行情。'},
      {id:'markets', title:'市场总览', icon:'▤', resource:'quotes', description:'查看已采集行情、来源和更新时间。'},
      {id:'calendar', title:'交易日历', icon:'▦', resource:'calendar', description:'查看计划、事件和提醒。'},
      {id:'indices', title:'大盘与指数', icon:'↗', resource:'indices', group:'市场研究', description:'查看主要指数及历史表现。'},
      {id:'news', title:'财经新闻', icon:'▧', resource:'news', group:'市场研究', description:'查看财经快讯及来源时间。'},
      {id:'liquidity', title:'央行流动性', icon:'◈', resource:'liquidity', group:'市场研究', description:'查看公开市场操作和流动性事件。'},
      {id:'flows', title:'资金流向', icon:'⇄', resource:'flows', group:'市场研究', description:'查看大盘、行业和北向资金资料。'},
      {id:'funds', title:'公募基金', icon:'▥', resource:null, group:'市场研究', description:'搜索基金目录、净值和披露资料。'},
      {id:'sectors', title:'板块轮动', icon:'▦', resource:'sectors', group:'市场研究', description:'查看行业强弱、轮动与成分股。'},
      {id:'gold', title:'黄金行情', icon:'◇', resource:null, group:'市场研究', description:'查看黄金报价和历史走势。'},
      {id:'research', title:'策略研究', icon:'▨', resource:'research', group:'研究工具', description:'查看策略实验、回测与研究记录。'},
      {id:'documents', title:'研报资料', icon:'▤', resource:'documents', group:'研究工具', description:'查看已导入的研报和财报。'},
      {id:'paper', title:'模拟炒股', icon:'◉', resource:'paper_local_accounts', group:'账户', description:'查看本地模拟账户。'},
      {id:'live', title:'富途实盘', icon:'◉', resource:'live_futu_accounts', group:'账户', description:'查看已连接的富途实盘账户。'},
      {id:'wiki', title:'投资记忆', icon:'▧', resource:'wiki_tree', description:'查看已归档的投资记忆。'},
      {id:'settings', title:'数据与设置', icon:'⚙', resource:'catalog', group:'设置', description:'查看数据库与插件状态。'}
    ];
    const workspaceGroups = [
      {title:'常用', ids:['guide','markets','holdings','watchlist','live']},
      {title:'市场', ids:['indices','news','liquidity','flows','funds','sectors','gold']},
      {title:'分析', ids:['research','documents','paper']},
    ];
    let selected = null;
    const listeners = new Set();
    function choose(id) { selected = id; for (const listener of listeners) listener(); }
    function subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); }
    function usePage() { return React.useSyncExternalStore(subscribe, () => selected, () => null); }

    const css = `
      .finfreedom-nav-mount{flex:none;min-width:0}.finfreedom-nav{min-width:0;padding:0 2px 8px;color:var(--dsw-alias-label-primary);font:inherit}
      .finfreedom-nav-title{font-size:11px;color:var(--dsw-alias-label-tertiary);padding:3px 8px 4px;letter-spacing:.03em}
      .finfreedom-nav button{font:inherit;cursor:pointer;color:var(--dsw-alias-label-secondary);background:transparent;border:0;border-radius:8px;display:flex;align-items:center;gap:10px;min-height:32px;width:100%;padding:5px 9px;text-align:left}
      .finfreedom-nav button:hover,.finfreedom-nav button[aria-current=page]{background:var(--dsw-alias-interactive-bg-hover);color:var(--dsw-alias-label-primary)}
      .finfreedom-nav button:focus-visible,.finfreedom-panel button:focus-visible,.finfreedom-panel input:focus-visible{outline:2px solid var(--dsw-alias-brand-primary);outline-offset:2px}
      .finfreedom-nav-icon{width:18px;text-align:center;font-size:16px;flex:none}.finfreedom-nav-more{max-height:min(43vh,360px);overflow:auto}.finfreedom-nav-group{font-size:11px;color:var(--dsw-alias-label-tertiary);padding:10px 9px 3px}
      .finfreedom-nav-caret{margin-left:auto}.finfreedom-nav.compact{padding:0 0 8px}.finfreedom-nav.compact button{width:36px;height:36px;justify-content:center;padding:0}
      .finfreedom-panel{position:fixed;top:0;right:0;bottom:0;z-index:10;pointer-events:auto;overflow:auto;background:var(--dsw-alias-bg-layer-1,#fff);color:var(--dsw-alias-label-primary,#20242b);font-family:inherit}
      .finfreedom-shell{max-width:1240px;margin:auto;padding:34px clamp(22px,4vw,56px) 70px}.finfreedom-top{display:flex;align-items:center;gap:12px;margin-bottom:30px}.finfreedom-back{border:1px solid var(--dsw-alias-border-l2,#e4e6ea);background:transparent;color:inherit;border-radius:9px;padding:8px 12px;cursor:pointer}.finfreedom-crumb{color:var(--dsw-alias-label-tertiary,#7a828d);font-size:13px}.finfreedom-header{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;margin-bottom:26px}.finfreedom-header h1{font-size:25px;line-height:1.3;margin:0 0 7px;letter-spacing:-.02em}.finfreedom-header p{font-size:14px;color:var(--dsw-alias-label-secondary,#616b77);margin:0;line-height:1.6}.finfreedom-badge{font-size:12px;white-space:nowrap;border:1px solid var(--dsw-alias-border-l2,#e4e6ea);border-radius:999px;padding:5px 10px;color:var(--dsw-alias-label-secondary,#616b77)}
      .finfreedom-card{border:1px solid var(--dsw-alias-border-l2,#e4e6ea);border-radius:14px;background:var(--dsw-alias-bg-layer-2,#fff);padding:24px;margin-bottom:16px}.finfreedom-card h2{font-size:16px;margin:0 0 10px}.finfreedom-muted{color:var(--dsw-alias-label-secondary,#616b77);font-size:13px;line-height:1.65}.finfreedom-empty{padding:32px 8px;text-align:center}.finfreedom-empty strong{display:block;margin-bottom:7px}.finfreedom-toolbar{display:flex;gap:10px;align-items:center;margin-bottom:16px}.finfreedom-toolbar input{font:inherit;color:inherit;background:transparent;border:1px solid var(--dsw-alias-border-l2,#e4e6ea);border-radius:9px;padding:9px 11px;max-width:300px;width:100%}.finfreedom-toolbar button{font:inherit;background:transparent;color:inherit;border:1px solid var(--dsw-alias-border-l2,#e4e6ea);border-radius:9px;padding:9px 13px;cursor:pointer}.finfreedom-table-wrap{overflow:auto}.finfreedom-table{border-collapse:collapse;width:100%;font-size:13px;text-align:left}.finfreedom-table th,.finfreedom-table td{padding:12px 10px;border-bottom:1px solid var(--dsw-alias-border-l2,#e4e6ea);white-space:nowrap}.finfreedom-table th{font-size:12px;color:var(--dsw-alias-label-secondary,#616b77);font-weight:500}.finfreedom-table td{font-variant-numeric:tabular-nums}.finfreedom-status{font-size:12px;color:var(--dsw-alias-label-secondary,#616b77);margin-top:15px}.finfreedom-alert{color:var(--dsw-alias-label-error,#b42318)}
      .finfreedom-accounts{display:grid;gap:16px}.finfreedom-account{padding:4px 0 18px;border-bottom:1px solid var(--dsw-alias-border-l2,#e4e6ea)}.finfreedom-account:last-child{border-bottom:0}.finfreedom-account h2{margin:0 0 16px}.finfreedom-metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:16px;margin:0 0 16px}.finfreedom-metrics dt{color:var(--dsw-alias-label-secondary,#616b77);font-size:12px}.finfreedom-metrics dd{margin:5px 0 0;font-size:18px;font-variant-numeric:tabular-nums}
      .finfreedom-tabs{display:flex;gap:6px;margin-bottom:24px;border-bottom:1px solid var(--dsw-alias-border-l2,#e4e6ea)}.finfreedom-tabs button{font:inherit;background:transparent;color:var(--dsw-alias-label-secondary,#616b77);border:0;border-bottom:2px solid transparent;padding:9px 14px;cursor:pointer}.finfreedom-tabs button[aria-pressed=true]{color:var(--dsw-alias-label-primary,#20242b);border-bottom-color:var(--dsw-alias-brand-primary,#4869e8)}.finfreedom-toolbar select{font:inherit;color:inherit;background:var(--dsw-alias-bg-layer-2,#fff);border:1px solid var(--dsw-alias-border-l2,#e4e6ea);border-radius:9px;padding:9px}
      .finfreedom-record-list{display:grid;gap:0}.finfreedom-record{display:flex;flex-direction:column;gap:5px;width:100%;text-align:left;font:inherit;background:transparent;color:inherit;border:0;border-bottom:1px solid var(--dsw-alias-border-l2,#e4e6ea);padding:14px 8px;cursor:pointer}.finfreedom-record:hover{background:var(--dsw-alias-interactive-bg-hover)}.finfreedom-record small{font-size:12px;color:var(--dsw-alias-label-secondary,#616b77)}.finfreedom-detail-head{display:flex;align-items:center;gap:14px;margin-bottom:20px}.finfreedom-detail-head h2{margin:0}.finfreedom-page-text{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.7;font:inherit}.finfreedom-page-actions{display:flex;align-items:center;gap:12px;margin-top:20px}.finfreedom-page-actions button:disabled{opacity:.45;cursor:default}.finfreedom-json{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;line-height:1.6}
      .finfreedom-original-panel{display:flex;flex-direction:column;overflow:hidden;background:#11151c}
      .finfreedom-original-bar{flex:none;padding:7px 12px;background:var(--dsw-alias-bg-layer-1,#fff);display:flex;justify-content:space-between;align-items:center;gap:12px}
      .finfreedom-appearance{display:flex;gap:3px;padding:3px;border:1px solid var(--dsw-alias-border-l2,#dce2e9);border-radius:9px}
      .finfreedom-appearance button{font:inherit;font-size:12px;border:0;border-radius:6px;padding:5px 10px;color:var(--dsw-alias-label-secondary,#616b77);background:transparent;cursor:pointer}
      .finfreedom-appearance button[aria-pressed=true]{background:var(--dsw-alias-interactive-bg-hover,#e8eaed);color:var(--dsw-alias-label-primary,#20242b)}
      .finfreedom-workspace-body{display:flex;flex:1;min-height:0;min-width:0;position:relative}
      .finfreedom-workspace-rail{flex:none;width:48px;position:relative;background:var(--dsw-alias-bg-layer-1,#fff);border-right:1px solid var(--dsw-alias-border-l2,#dce2e9)}
      .finfreedom-workspace-nav{position:absolute;z-index:2;inset:0 auto 0 0;box-sizing:border-box;display:flex;flex-direction:column;width:48px;overflow-y:auto;overflow-x:hidden;padding:6px 4px;background:var(--dsw-alias-bg-layer-1,#fff);border-right:1px solid var(--dsw-alias-border-l2,#dce2e9);scrollbar-width:thin;transition:width .15s ease}
      .finfreedom-workspace-nav:hover,.finfreedom-workspace-nav:focus-within{width:190px;box-shadow:6px 0 18px rgba(0,0,0,.12)}
      .finfreedom-workspace-nav > section,.finfreedom-workspace-brand,.finfreedom-workspace-footer{flex-shrink:0}
      .finfreedom-workspace-footer{margin-top:auto;padding-top:10px;border-top:1px solid var(--dsw-alias-border-l2,#dce2e9)}
      .finfreedom-workspace-brand{display:flex;align-items:center;gap:10px;height:38px;padding:0 6px;white-space:nowrap;overflow:hidden;color:var(--dsw-alias-label-primary,#20242b)}
      .finfreedom-workspace-brand img{display:block;flex:none;width:24px;height:24px;border-radius:6px}
      .finfreedom-workspace-brand span{font-size:14px;font-weight:650;letter-spacing:-.02em;opacity:0;transition:opacity .1s}
      .finfreedom-workspace-group-label{height:19px;display:flex;align-items:center;padding:0 10px;color:var(--dsw-alias-label-tertiary,#8c929a);font-size:11px;white-space:nowrap;overflow:hidden}
      .finfreedom-workspace-group-label span{opacity:0;transition:opacity .1s}
      .finfreedom-workspace-group-label::before{content:'';display:block;width:16px;border-top:1px solid var(--dsw-alias-border-l2,#dce2e9);flex:none}
      .finfreedom-workspace-nav:hover .finfreedom-workspace-group-label::before,.finfreedom-workspace-nav:focus-within .finfreedom-workspace-group-label::before{display:none}
      .finfreedom-workspace-nav:hover .finfreedom-workspace-group-label span,.finfreedom-workspace-nav:focus-within .finfreedom-workspace-group-label span,.finfreedom-workspace-nav:hover .finfreedom-workspace-brand span,.finfreedom-workspace-nav:focus-within .finfreedom-workspace-brand span{opacity:1}
      .finfreedom-workspace-nav button{display:flex;align-items:center;gap:10px;box-sizing:border-box;width:100%;height:36px;border:0;border-radius:8px;background:transparent;color:var(--dsw-alias-label-secondary,#616b77);font:inherit;font-size:13px;padding:8px 10px;white-space:nowrap;cursor:pointer;text-align:left}
      .finfreedom-workspace-nav button span{opacity:0;transition:opacity .1s;pointer-events:none}
      .finfreedom-workspace-nav:hover button span,.finfreedom-workspace-nav:focus-within button span{opacity:1}
      .finfreedom-workspace-nav button:hover,.finfreedom-workspace-nav button[aria-current=page]{background:var(--dsw-alias-interactive-bg-hover,#e8eaed);color:var(--dsw-alias-label-primary,#20242b)}
      .finfreedom-workspace-nav button:focus-visible{outline:2px solid var(--dsw-alias-brand-primary,#4869e8);outline-offset:-2px}
      .finfreedom-workspace-nav .finfreedom-nav-icon{width:16px;height:16px;flex:none}
      .finfreedom-original-frame{display:block;flex:1;min-width:0;min-height:0;height:100%;border:0;background:#11151c}
      @media (prefers-reduced-motion:reduce){.finfreedom-workspace-nav,.finfreedom-workspace-nav button span,.finfreedom-workspace-group-label span,.finfreedom-workspace-brand span{transition:none}}
      @media(max-width:640px){.finfreedom-shell{padding:24px 18px 60px}.finfreedom-header{display:block}.finfreedom-badge{display:inline-block;margin-top:12px}.finfreedom-card{padding:17px}}
    `;

    function Nav({wide, onExpand}) {
      const active = usePage();
      const [mount, setMount] = React.useState(null);
      const [placementReady, setPlacementReady] = React.useState(false);
      const anchor = React.useRef(null);
      // DSH 0.1.1-rc.2 only exposes a footer slot. Place a portal before
      // its workspace region so visual and keyboard order remain identical.
      React.useLayoutEffect(() => {
        const root = anchor.current?.closest('.hHd-Xa_root');
        const region = root?.querySelector(':scope > .hHd-Xa_regionArea');
        if (!root || !region) { setPlacementReady(true); return; }
        const target = document.createElement('div'); target.className = 'finfreedom-nav-mount';
        root.insertBefore(target, region); setMount(target); setPlacementReady(true);
        return () => target.remove();
      }, []);
      const button = page => h('button', {key:page.id, type:'button', title:page.title,
        'aria-current':active === page.id ? 'page' : undefined, onClick:() => choose(page.id)},
        h(Icon, {name:pageIcons[page.id]}), wide && h('span', null, page.title));
      const nav = h('nav', {className:`finfreedom-nav${wide ? '' : ' compact'}`, 'aria-label':'finfreedom 工作台'},
        wide && h('div', {className:'finfreedom-nav-title'}, 'FINFREEDOM 工作台'),
        ...['guide','markets','holdings','watchlist'].map(id => button(pages.find(page => page.id === id))),
        h('button', {type:'button', title:'工作台', onClick:() => choose('indices')},
          h(Icon, {name:'grid'}), wide && h('span', null, '工作台')));
      return h(React.Fragment, null, h('span', {ref:anchor, hidden:true}), mount ? ReactDOM.createPortal(nav, mount) : placementReady && nav);
    }

    const labels = {instrument_id:'标的',name:'名称',symbol:'代码',market:'市场',last:'价格',currency:'币种',
      received_at:'接收时间',exchange_time:'行情时间',provider:'来源',freshness:'时效',quantity:'数量',
      current_value:'参考市值',valuation_source:'估值方式',quote_time:'行情接收时间',asset_class:'资产类别',cost_basis:'成本',manual_value:'记录市值',cash:'现金',principal:'本金',updated_at:'更新时间',filename:'文件名',
      document_type:'类型',page_count:'页数',imported_at:'导入时间',question:'问题',status:'状态',
      created_at:'创建时间',strategy_id:'策略',run_id:'记录编号',instrument:'标的',id:'指数',
      change_percent:'涨跌幅 %',source:'来源',source_time:'行情时间',as_of:'更新时间',groups:'自选分组',
      account_suffix:'账户尾号',equity:'总资产',sellable:'可卖数量',average_cost:'平均成本',market_value:'市值'};
    function cell(value) {
      if (value == null) return '—';
      if (value === 'stale') return '历史缓存';
      if (value === 'unknown') return '时效待确认';
      if (value === 'fresh') return '较新';
      if (typeof value === 'object') return Array.isArray(value) ? (value.every(item => typeof item === 'string') ? value.join('、') : `${value.length} 项`) : '结构化数据';
      return String(value);
    }
    function Table({rows}) {
      const all = [...new Set(rows.flatMap(row => Object.keys(row)))].filter(k => k !== 'positions');
      const preferred = ['instrument_id','id','name','market','last','currency','change_percent','quantity','current_value','valuation_source','sellable','average_cost','market_value','exchange_time','source_time','quote_time','provider','source','freshness','groups'];
      const keys = [...preferred.filter(key => all.includes(key)), ...all.filter(key => !preferred.includes(key))].slice(0, 12);
      return h('div', {className:'finfreedom-table-wrap'}, h('table', {className:'finfreedom-table'},
        h('thead', null, h('tr', null, ...keys.map(k => h('th', {key:k, scope:'col'}, labels[k] || k)))),
        h('tbody', null, ...rows.map((row,i) => h('tr', {key:row.instrument_id || row.run_id || row.document_id || i},
          ...keys.map(k => h('td', {key:k}, cell(row[k]))))))));
    }
    function Portfolios({accounts}) {
      const money = value => value == null ? '—' : Number(value).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
      return h('div', {className:'finfreedom-accounts'}, ...accounts.map(account =>
        h('section', {className:'finfreedom-account', key:account.currency}, h('h2', null, `${account.currency} 账户`),
          h('dl', {className:'finfreedom-metrics'}, ...[['总资产',account.total_assets],['持仓市值',account.holdings_value],['现金',account.cash],['本金',account.principal]].map(([label,value]) =>
            h('div', {key:label}, h('dt', null, label), h('dd', null, money(value))))),
          account.positions?.length ? h(Table, {rows:account.positions}) : h('p', {className:'finfreedom-muted'}, account.updated_at ? '暂无持仓明细。' : '还没有持仓记录。可在 DSH 对话中提供资料生成核对草稿；工作台保存入口尚未接入。'),
          account.updated_at && h('div', {className:'finfreedom-status'}, `持仓更新时间：${account.updated_at} · 行情可能为历史缓存，请查看明细时效${account.valuation_complete ? '' : ' · 部分持仓缺少市值，暂不计算总资产'}`))));
    }
    function FutuAccounts({accounts}) {
      const money = value => value == null ? '—' : Number(value).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2});
      return h('div', {className:'finfreedom-accounts'}, ...accounts.map(account =>
        h('section', {className:'finfreedom-account', key:account.id},
          h('h2', null, `富途 ${account.market} · ${account.mode === 'REAL' ? '实盘' : '模拟'} · 尾号 ${account.account_suffix}`),
          h('dl', {className:'finfreedom-metrics'}, ...[['总资产',account.equity],['现金',account.cash]].map(([label,value]) =>
            h('div', {key:label}, h('dt', null, `${label} · ${account.currency}`), h('dd', null, money(value))))),
          account.positions?.length ? h(Table, {rows:account.positions}) : h('p', {className:'finfreedom-muted'}, account.state === 'partial' ? '持仓查询未完成，请检查 OpenD 账户权限。' : '该账户暂无持仓。'),
          h('div', {className:'finfreedom-status'}, `来源：富途 OpenD · 查询时间：${account.as_of || '未知'} · ${account.state === 'partial' ? '部分数据不可用' : '只读'}`))));
    }
    async function fetchResource(resource, query, signal, market, extra = {}) {
      const params = new URLSearchParams({resource});
      if (query) params.set('query', query);
      if (market) params.set('market', market);
      for (const [key,value] of Object.entries(extra)) params.set(key, String(value));
      const response = await fetch(`/finfreedom/api/read?${params}`, {headers:{'X-finfreedom-Client':'1'}, signal});
      const body = await response.json();
      if (!response.ok) throw new Error(body.error || '数据暂不可用。');
      const value = body.data;
      return value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).length === 1 && 'result' in value ? value.result : value;
    }
    function DocumentBrowser({rows}) {
      const [selectedDoc, setSelectedDoc] = React.useState(null);
      const [pageNumber, setPageNumber] = React.useState(1);
      const [result, setResult] = React.useState(null);
      const [error, setError] = React.useState('');
      const [retry, setRetry] = React.useState(0);
      React.useEffect(() => {
        if (!selectedDoc) return;
        const abort = new AbortController(); setResult(null); setError('');
        fetchResource('document_page', '', abort.signal, '', {document_id:selectedDoc.document_id, page:pageNumber})
          .then(setResult).catch(e => {if (e.name !== 'AbortError') setError(e.message);});
        return () => abort.abort();
      }, [selectedDoc, pageNumber, retry]);
      if (!selectedDoc) return h('div', {className:'finfreedom-record-list'}, ...rows.map(row =>
        h('button', {className:'finfreedom-record', key:row.document_id, type:'button', onClick:() => {setPageNumber(1); setSelectedDoc(row);}},
          h('strong', null, row.filename), h('small', null, `${row.document_type} · ${row.page_count} 页 · 导入 ${row.imported_at}`))));
      return h('div', null, h('div', {className:'finfreedom-detail-head'},
        h('button', {className:'finfreedom-back', type:'button', onClick:() => setSelectedDoc(null)}, '← 返回资料列表'), h('h2', null, selectedDoc.filename)),
        error ? h('div', {role:'alert', className:'finfreedom-alert'}, error, ' ', h('button', {className:'finfreedom-back', type:'button', onClick:() => setRetry(retry + 1)}, '重试'))
          : !result ? h('p', {className:'finfreedom-muted', role:'status'}, '正在读取资料页…') : h(React.Fragment, null, h('p', {className:'finfreedom-muted'}, '每页最多显示 12000 字。'), h('div', {className:'finfreedom-page-text'}, result.content || '该页没有提取到文字。')),
        h('div', {className:'finfreedom-page-actions'},
          h('button', {className:'finfreedom-back', type:'button', disabled:pageNumber <= 1, onClick:() => setPageNumber(pageNumber - 1)}, '上一页'),
          h('span', {className:'finfreedom-muted'}, `第 ${pageNumber} / ${selectedDoc.page_count} 页`),
          h('button', {className:'finfreedom-back', type:'button', disabled:pageNumber >= Math.min(500, selectedDoc.page_count), onClick:() => setPageNumber(pageNumber + 1)}, '下一页')),
        selectedDoc.page_count > 500 && h('p', {className:'finfreedom-muted'}, '目前最多读取前 500 页。'));
    }
    function ResearchBrowser({rows}) {
      const [selectedRun, setSelectedRun] = React.useState(null);
      const [result, setResult] = React.useState(null);
      const [error, setError] = React.useState('');
      const [retry, setRetry] = React.useState(0);
      React.useEffect(() => {
        if (!selectedRun) return;
        const abort = new AbortController(); setResult(null); setError('');
        fetchResource('research', '', abort.signal, '', {run_id:selectedRun.run_id})
          .then(setResult).catch(e => {if (e.name !== 'AbortError') setError(e.message);});
        return () => abort.abort();
      }, [selectedRun, retry]);
      if (!selectedRun) return h('div', {className:'finfreedom-record-list'}, ...rows.map(row =>
        h('button', {className:'finfreedom-record', key:row.run_id, type:'button', onClick:() => setSelectedRun(row)},
          h('strong', null, row.question), h('small', null, `${row.status} · ${row.created_at}`))));
      return h('div', null, h('div', {className:'finfreedom-detail-head'},
        h('button', {className:'finfreedom-back', type:'button', onClick:() => setSelectedRun(null)}, '← 返回研究记录'), h('h2', null, selectedRun.question)),
        error ? h('div', {role:'alert', className:'finfreedom-alert'}, error, ' ', h('button', {className:'finfreedom-back', type:'button', onClick:() => setRetry(retry + 1)}, '重试'))
          : !result ? h('p', {className:'finfreedom-muted', role:'status'}, '正在读取研究记录…')
          : h(React.Fragment, null, h('p', {className:'finfreedom-muted'}, `状态：${result.status} · 创建时间：${result.created_at}`),
              h('div', {className:'finfreedom-page-text'}, result.answer || '暂无研究正文。'),
              h('h2', null, '研究证据'), result.evidence?.length ? h('pre', {className:'finfreedom-json'}, JSON.stringify(result.evidence, null, 2)) : h('p', {className:'finfreedom-muted'}, '没有已保存的证据。')));
    }
    function BacktestBrowser({rows}) {
      const [selectedRun, setSelectedRun] = React.useState(null);
      if (!selectedRun) return h('div', {className:'finfreedom-record-list'}, ...rows.map(row =>
        h('button', {className:'finfreedom-record', key:row.run_id, type:'button', onClick:() => setSelectedRun(row)},
          h('strong', null, `${row.instrument_id} · ${row.strategy_id}`), h('small', null, `${row.created_at} · ${row.strategy_version}`))));
      return h('div', null, h('div', {className:'finfreedom-detail-head'},
        h('button', {className:'finfreedom-back', type:'button', onClick:() => setSelectedRun(null)}, '← 返回回测记录'), h('h2', null, `${selectedRun.instrument_id} · ${selectedRun.strategy_id}`)),
        h('p', {className:'finfreedom-muted'}, `数据集 ${selectedRun.dataset_version} · ${selectedRun.created_at}`),
        h('h2', null, '回测指标'), h('pre', {className:'finfreedom-json'}, JSON.stringify(selectedRun.metrics, null, 2)),
        h('h2', null, '策略参数'), h('pre', {className:'finfreedom-json'}, JSON.stringify(selectedRun.parameters, null, 2)));
    }
    function Workspace({sendToAgent}) {
      const id = usePage();
      const page = pages.find(item => item.id === id);
      const [left, setLeft] = React.useState(280);
      const main = React.useRef(null);
      const hadPage = React.useRef(false);
      const frame = React.useRef(null);
      const [appearance, setAppearance] = React.useState(() => { try { return localStorage.getItem('finfreedom.workspace.appearance') || 'light'; } catch (_) { return 'light'; } });
      const changeAppearance = value => {
        setAppearance(value);
        try { localStorage.setItem('finfreedom.workspace.appearance', value); } catch (_) {}
        frame.current?.contentWindow?.postMessage({type:'finfreedom-theme', value}, location.origin);
      };
      React.useEffect(() => {
        const onMessage = async event => {
          if (event.origin !== location.origin || event.source !== frame.current?.contentWindow) return;
          const type = event.data?.type;
          if (type !== 'finfreedom-install-futu' && type !== 'finfreedom-ask-agent') return;
          const question = type === 'finfreedom-install-futu'
            ? '请使用 install-futu-opend Skill 检查并安装富途 OpenD。先检查本机已有服务与登录状态，已有可用服务时不要重复安装；如果需要安装，请按 Skill 使用官方来源，并由我在 OpenD 中完成登录。完成后验证 finfreedom 的数据连接。'
            : String(event.data.question || '').slice(0,20000);
          if (!question) return;
          try { await sendToAgent(question); choose(null); }
          catch { frame.current?.contentWindow?.postMessage({type:'finfreedom-agent-error',message:'无法连接 DSH 会话，请检查连接后重试。'},location.origin); }
        };
        window.addEventListener('message',onMessage);
        return () => window.removeEventListener('message',onMessage);
      }, [sendToAgent]);
      React.useEffect(() => {
        const sidebar = document.querySelector('.hHd-Xa_root');
        if (!sidebar) return;
        const update = () => setLeft(Math.max(0, sidebar.getBoundingClientRect().right));
        update(); const observer = new ResizeObserver(update); observer.observe(sidebar);
        window.addEventListener('resize', update);
        return () => { observer.disconnect(); window.removeEventListener('resize', update); };
      }, []);
      React.useEffect(() => {
        if (!id) { hadPage.current = false; return; }
        const columns = [...document.querySelectorAll('.pI_x6G_centerCol, .pI_x6G_detailsCol')];
        const previous = columns.map(node => node.inert);
        columns.forEach(node => { node.inert = true; });
        if (!hadPage.current) main.current?.focus();
        hadPage.current = true;
        return () => columns.forEach((node, index) => { node.inert = previous[index]; });
      }, [id]);
      if (!page) return null;
      const routes = {paper:'paper', wiki:'memory'};
      const route = routes[id] || id;
      return h('section', {className:'finfreedom-panel finfreedom-original-panel', style:{left:`${left}px`}, 'aria-label':`${page.title} · finfreedom`},
        h('div', {className:'finfreedom-original-bar', ref:main, tabIndex:-1},
          h('button', {className:'finfreedom-back', type:'button', onClick:() => choose(null)}, '← 返回 DSH 对话'),
          h('div', {className:'finfreedom-appearance', role:'group', 'aria-label':'工作台外观'},
            ...[['light','浅色'],['dark','深色']].map(([value,label]) => h('button', {key:value, type:'button', 'aria-pressed':appearance === value, onClick:() => changeAppearance(value)}, label)))),
        h('div', {className:'finfreedom-workspace-body'},
          h('div', {className:'finfreedom-workspace-rail'},
            h('nav', {className:'finfreedom-workspace-nav', 'aria-label':'finfreedom 工作台导航'},
              h('div', {className:'finfreedom-workspace-brand'},
                h('img', {src:'/finfreedom/original/finfreedom-mark.svg',alt:'',width:24,height:24}),
                h('span', null, 'finfreedom')),
              ...workspaceGroups.map(group => h('section', {key:group.title, 'aria-label':group.title},
                h('div', {className:'finfreedom-workspace-group-label', 'aria-hidden':true}, h('span', null, group.title)),
                ...group.ids.map(pageId => {
                  const item = pages.find(page => page.id === pageId);
                  return h('button', {key:item.id, type:'button', title:item.title, 'aria-label':item.title,
                    'aria-current':id === item.id ? 'page' : undefined, onClick:() => choose(item.id)},
                    h(Icon, {name:pageIcons[item.id]}), h('span', {'aria-hidden':true}, item.title));
                }))),
              h('div', {className:'finfreedom-workspace-footer'},
                h('button', {type:'button', title:'数据与设置', 'aria-label':'数据与设置',
                  'aria-current':id === 'settings' ? 'page' : undefined, onClick:() => choose('settings')},
                  h(Icon, {name:pageIcons.settings}), h('span', {'aria-hidden':true}, '数据与设置'))))),
          h('iframe', {ref:frame, key:id, className:'finfreedom-original-frame', title:`${page.title} · finfreedom`, src:id === 'guide' ? '/finfreedom/original/guide.html' : `/finfreedom/original/index.html#/${route}`})));
    }

    function apply(ctx) {
      const sendToAgent = async question => {
        // Every workspace action opens an unclassified session with an editable
        // prompt, leaving the user's current conversation and draft untouched.
        const created = await ctx.sessions.create();
        if (created?.ok === false) throw new Error(created.error?.message || '无法创建 DSH 会话');
        const id = typeof created === 'string' ? created : created?.value?.sessionId ?? created?.sessionId;
        if (typeof id !== 'string' || !id) throw new Error('DSH 未返回新会话编号');

        // DSH 0.2.1 requires a retained Client Session before its Agent scope
        // exists. In 0.1.1, create() installs the scope immediately.
        const reference = typeof ctx.sessions.retain === 'function'
          ? ctx.sessions.retain(id, {source:'mainView'})
          : null;
        try {
          if (reference?.ready) await reference.ready;
          const scoped = ctx.sessions.scope(id);
          if (!scoped) throw new Error('DSH 会话不可用');
          const input = ctx.conversation.input.for(scoped);
          input.setDraft(question);
          const workspace = ctx.get?.('uiWorkspace');
          if (typeof workspace?.openSession === 'function') workspace.openSession(id);
          else if (typeof ctx.sessions.open === 'function') ctx.sessions.open(id);
          else throw new Error('当前 DSH 版本不支持打开新会话');
        } finally {
          reference?.release?.();
        }
      };
      ctx.effect(() => {
        const style = document.createElement('style'); style.dataset.plugin = '@finfreedom/dsh-plugin'; style.textContent = css;
        document.head.appendChild(style);
        const reset = event => { if (event.target.closest('.hHd-Xa_regionArea,.hHd-Xa_newSession')) choose(null); };
        document.addEventListener('click', reset, true);
        return () => { document.removeEventListener('click', reset, true); style.remove(); };
      }, 'finfreedom: styles and navigation');
      ctx.slots.inject('sidebar.footer.action', () => ctx.slots.register({name:'sidebar.footer.action', id:'finfreedom-navigation', inject:() => ({onExpand:() => ctx.layout.toggleSidebar()})}, Nav));
      ctx.slots.inject('shell.overlay', () => ctx.slots.register({name:'shell.overlay', id:'finfreedom-workspace', inject:() => ({sendToAgent})}, Workspace));
    }
    return {inject:['slots', 'layout', 'sessions', 'conversation'], apply};
  }
});
