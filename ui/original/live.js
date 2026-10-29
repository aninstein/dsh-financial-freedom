import { request } from './api.js';
import { esc, money, number, time, empty, notify } from './ui.js';

export async function renderLive(_route, signal, ui) {
  const state = await request('/live/status', {signal});
  if (signal.aborted) return;
  const accounts = Array.isArray(state.accounts) ? state.accounts : [];
  const connected = state.opend_reachable && !['unavailable','disabled'].includes(state.state);
  const note = !state.opend_reachable ? '未连接本机 OpenD，请先启动并登录富途 OpenD。'
    : state.state === 'unavailable' || state.state === 'disabled' ? 'OpenD 已监听，但账户目录暂不可用，请检查登录与连接设置。'
    : state.state === 'partial' ? '部分市场账户读取失败，请检查 OpenD 后重试。'
    : accounts.length ? '已读取 OpenD 账户目录。选择允许读取的账户后，可以查看资金和持仓。'
    : 'OpenD 已连接，但没有返回可用的港股或美股真实账户。请检查 OpenD 登录的账号及账户权限。';
  const rows = accounts.map(a => `<label class="check-row section-gap"><input type="checkbox" name="account" value="${esc(a.id)}" ${a.authorized ? 'checked' : ''} ${a.managed_by_env ? 'disabled' : ''}/><span>${esc(a.market)} 真实账户 · 尾号 ${esc(a.account_suffix)}${a.managed_by_env ? '（由服务端配置）' : ''}</span></label>`).join('');
  const permitted = accounts.filter(a => a.authorized);
  ui.setPage(ui.page(ui.heading('富途实盘', '查看 OpenD 真实账户的资金与持仓。', `<button class="button" data-action="live-refresh">刷新连接状态</button>`) +
    `<div class="alert"><strong>${connected ? 'OpenD 已连接' : 'OpenD 连接待检查'}</strong><p>${esc(note)}</p><p>当前支持只读查询；实盘委托和撤单尚未接入 DSH。</p></div>` +
    `<div class="section-gap split">${ui.panel('账户读取设置', `<form id="live-access-form" class="panel-body" novalidate><p class="field-help">选择允许本机工作台读取的账户。仅显示账户尾号；修改不影响券商交易权限。</p>${rows || `<p class="field-help section-gap">${esc(note)}</p>`}<div class="form-error" id="live-access-error" role="alert"></div>${accounts.length ? '<button class="button primary section-gap" type="submit">保存读取设置</button>' : ''}</form>`)}${ui.panel('真实账户与持仓', `<div class="panel-body"><label class="field-label" for="live-connection">选择已授权账户</label><select class="field" id="live-connection">${permitted.length ? permitted.map(a => `<option value="${esc(a.id)}">${esc(a.market)} · 尾号 ${esc(a.account_suffix)}</option>`).join('') : '<option value="">暂无已授权账户</option>'}</select><button class="button section-gap" data-action="live-account" ${permitted.length ? '' : 'disabled'}>查询账户</button><div id="live-account-view" class="section-gap" aria-live="polite">${empty('尚未查询真实账户', permitted.length ? '选择账户并点击查询。' : '选择允许读取的账户并保存设置。')}</div></div>`)}</div>` +
    `<section class="panel section-gap"><div class="panel-header"><h2>实盘委托</h2></div><div class="panel-body"><p class="field-help">实盘委托查询、下单与撤单尚未接入 DSH；请在富途客户端查看及操作。</p></div></section>`));
}

export async function handleLiveSubmit(form, _values, ui) {
  if (form.id !== 'live-access-form') return false;
  await ui.busy(form, async () => {
    try {
      const account_ids = [...form.querySelectorAll('input[name="account"]:checked:not(:disabled)')].map(x => x.value);
      await request('/live/read-access', {method:'PUT',body:{account_ids}});
      notify('账户读取设置已保存');
      await ui.renderRoute();
    } catch (error) { ui.formError('live-access-error',error.message); }
  });
  return true;
}

export async function handleLiveAction(button, ui) {
  if (!button.dataset.action?.startsWith('live-')) return false;
  button.disabled = true;
  try {
    if (button.dataset.action === 'live-refresh') { await request('/live/status?refresh=1'); await ui.renderRoute(); return true; }
    if (button.dataset.action === 'live-account') {
      const identifier = document.querySelector('#live-connection').value;
      const target = document.querySelector('#live-account-view');
      target.innerHTML = '<p class="field-help" role="status">正在读取账户…</p>';
      try {
        const a = await request('/live/accounts/' + encodeURIComponent(identifier), {timeout:45000});
        const positions=Array.isArray(a.positions) ? a.positions : [];
        target.innerHTML = `<h3>${esc(a.market)} 真实账户 · 尾号 ${esc(a.account_suffix)}</h3><p class="paper-balance section-gap">${money(a.cash,a.currency)}</p><p class="field-help">可用现金 · ${esc(a.currency)} · 查询时间 ${time(a.as_of)}</p>${a.state === 'partial' ? '<p class="field-help">部分资金或持仓未能读取，请在富途核对。</p>' : ''}${positions.length ? `<div class="table-scroll section-gap"><table class="data-table"><thead><tr><th>股票</th><th>数量 / 可卖</th><th>成本</th><th>市值</th></tr></thead><tbody>${positions.map(p=>`<tr><td>${esc(p.name || p.instrument_id)}<small>${esc(p.instrument_id)}</small></td><td>${number(p.quantity)} / ${number(p.sellable)}</td><td>${number(p.average_cost,4)}</td><td>${money(p.market_value,a.currency)}</td></tr>`).join('')}</tbody></table></div>` : a.state === 'partial' ? '' : empty('暂无持仓','以富途返回为准。')}`;
      } catch (error) {target.textContent = '读取账户失败：' + error.message;}
    }
  } catch (error) { notify(error.message); } finally {button.disabled = false;}
  return true;
}
