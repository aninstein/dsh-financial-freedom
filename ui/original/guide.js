const content=document.getElementById('guide-content');
const feedback=document.getElementById('guide-feedback');
const dialog=document.getElementById('entry-dialog');
const form=document.getElementById('entry-form');
const editor=document.getElementById('entry-markdown');
const error=document.getElementById('editor-error');
const search=document.getElementById('entry-search');
const category=document.getElementById('entry-category');
const count=document.getElementById('entry-count');
const recContent=document.getElementById('recommendations-content');
const recStatus=document.getElementById('recommendations-status');
const recRefresh=document.getElementById('recommendations-refresh');
let view='recommendations', version=0, entries=[], editing=null, busy=false, launching=false, generation=0;

async function api(method, payload) {
  const options={method,headers:{'X-Finfreedom-Client':'1'}};
  if(payload){options.headers['Content-Type']='application/json';options.body=JSON.stringify(payload);}
  const response=await fetch('/finfreedom/api/guide'+(method==='GET'?`?view=${encodeURIComponent(view==='recommendations'?'favorites':view)}`:''),options);
  const body=await response.json();if(!response.ok)throw new Error(body.error || '词条服务暂不可用');return body.data;
}
function description(markdown){return markdown.split('\n').map(x=>x.trim()).find(x=>x&&!x.startsWith('#')&&!x.startsWith('- ')) || '打开词条，使用这份研究提示词。';}
function button(label, className, action){const b=document.createElement('button');b.type='button';b.className=className;b.setAttribute('aria-label',label);b.title=label;b.addEventListener('click',action);return b;}
function render(){
  content.replaceChildren();
  count.textContent=`${entries.length} 个词条`;
  if(!entries.length){const empty=document.createElement('p');empty.className='empty';empty.textContent=view==='favorites'?'还没有收藏。打开“内置词条”，收藏常用的研究方法。':view==='mine'?'还没有自己的词条。新建词条，或编辑一个内置词条。':'暂无内置词条。';content.append(empty);if(view==='favorites'){const show=button('查看内置词条','subtle',()=>document.querySelector('[data-view=all]').click());show.textContent='查看内置词条 →';content.append(show);}return;}
  const term=search.value.trim().toLocaleLowerCase();
  const filtered=entries.filter(item=>(!category.value || item.group===category.value) && (!term || [item.title,item.markdown,item.group,item.skill_origin].some(value=>String(value||'').toLocaleLowerCase().includes(term))));
  count.textContent=`${filtered.length} / ${entries.length} 个词条`;
  if(!filtered.length){const empty=document.createElement('p');empty.className='empty';empty.textContent='没有匹配的词条，请尝试其他关键词或分类。';content.append(empty);return;}
  const groups=new Map();
  for(const item of filtered){const name=item.group || (item.source==='mine'?'个人词条':'其他');if(!groups.has(name))groups.set(name,[]);groups.get(name).push(item);}
  for(const [name,items] of groups){
    const section=document.createElement('section');section.className='entry-group';
    const heading=document.createElement('h2');heading.className='group-title';heading.textContent=name;
    const count=document.createElement('span');count.className='group-count';count.textContent=`${items.length} 个词条`;heading.append(count);section.append(heading);
    const grid=document.createElement('div');grid.className='grid';
    for(const item of items){
      const card=document.createElement('article');card.className='card';
      if(item.is_new){const badge=document.createElement('span');badge.className='new-badge';badge.setAttribute('aria-label','新上线');badge.textContent='✦ 新';card.append(badge);}
      const open=button(`在 DSH 对话中使用：${item.title}`,'card-main',()=>{
        if(launching)return; launching=true;feedback.textContent='正在打开 DSH 对话…';
        window.parent.postMessage({type:'finfreedom-ask-agent',question:item.markdown},location.origin);
        setTimeout(()=>{if(launching){launching=false;feedback.textContent='未能打开 DSH 对话，请重试。';}},15000);
      });
      const title=document.createElement('h3');title.textContent=item.title;
      const desc=document.createElement('p');desc.className='description';desc.textContent=description(item.markdown);open.append(title,desc);
      const meta=document.createElement('div');meta.className='card-meta';
      const origin=document.createElement('span');origin.textContent=item.source==='mine'?'我的词条':item.skill_origin || '内置词条';
      const edit=button(`编辑：${item.title}`,'icon-button',()=>openEditor(item));edit.textContent='编辑';
      const favorite=button(`${item.favorite?'取消收藏':'收藏'}：${item.title}`,'icon-button favorite',()=>change(item.favorite?'unfavorite':'favorite',{id:item.id}));
      favorite.textContent=item.favorite?'★':'☆';favorite.setAttribute('aria-pressed',String(item.favorite));
      meta.append(origin,edit,favorite);card.append(open,meta);grid.append(card);
    }
    section.append(grid);content.append(section);
  }
}
async function load(){
  const request=++generation;
  feedback.textContent='正在加载词条…';content.replaceChildren();
  try {const data=await api('GET');if(request!==generation)return;version=data.version;entries=data.entries;const previous=category.value;category.replaceChildren();const all=document.createElement('option');all.value='';all.textContent='全部分类';category.append(all);for(const name of [...new Set(entries.map(item=>item.group).filter(Boolean))]){const option=document.createElement('option');option.value=name;option.textContent=name;category.append(option);}category.value=[...category.options].some(option=>option.value===previous)?previous:'';feedback.textContent='';render();}
  catch(e){if(request!==generation)return;feedback.textContent=`加载失败：${e.message}`;const retry=button('重试','subtle',load);retry.textContent='重试';content.append(retry);}
}
async function change(action,data){
  if(busy)return false;busy=true;feedback.textContent='正在保存…';
  try {await api('POST',{action,data:{...data,expected_version:version}});await load();return true;}
  catch(e){feedback.textContent=`保存失败：${e.message}`;return false;}
  finally{busy=false;}
}
function openEditor(item){editing=item;editor.value=item?.markdown || '# 新词条\n\n## 提示词\n\n';document.getElementById('editor-title').textContent=item?'编辑词条':'新建词条';error.textContent='';dialog.showModal();editor.focus();}
search.addEventListener('input',render);category.addEventListener('change',render);
function selectView(next){
  view=next;category.value='';
  document.querySelector('.recommendations').hidden=next!=='recommendations';
  document.querySelector('.filters').hidden=next==='recommendations';
  content.hidden=next==='recommendations';
  for(const tab of document.querySelectorAll('[data-view]'))tab.setAttribute('aria-current',tab.dataset.view===next?'page':'false');
  load();
}
for(const tab of document.querySelectorAll('[data-view]'))tab.addEventListener('click',()=>{if(!busy)selectView(tab.dataset.view);});
document.getElementById('create-entry').addEventListener('click',()=>openEditor(null));
document.getElementById('editor-close').addEventListener('click',()=>dialog.close());
document.getElementById('editor-cancel').addEventListener('click',()=>dialog.close());
form.addEventListener('submit',async event=>{event.preventDefault();if(!/^#\s+\S/m.test(editor.value)){error.textContent='请使用一级标题，例如：# 我的投研词条';return;}error.textContent='';const ok=await change(editing && !editing.recommendation?'update':'create',{...(editing && !editing.recommendation?{id:editing.id}:{}),markdown:editor.value});if(ok){dialog.close();selectView('mine');}else error.textContent=feedback.textContent;});
function setTheme(value){document.documentElement.dataset.workspaceTheme=value==='dark'?'dark':'light';}
try{setTheme(localStorage.getItem('finfreedom.workspace.appearance'));}catch{setTheme('light');}
window.addEventListener('message',event=>{if(event.origin!==location.origin||event.source!==window.parent)return;if(event.data?.type==='finfreedom-theme')setTheme(event.data.value);if(event.data?.type==='finfreedom-agent-error'){launching=false;feedback.textContent=event.data.message||'无法打开 DSH 对话，请重试。';}});
selectView('recommendations');

async function loadRecommendations(){
  try {
    const response=await fetch('/finfreedom/api/recommendations',{headers:{'X-Finfreedom-Client':'1'}});
    const result=await response.json(); if(!response.ok)throw Error(result.error||'推荐暂不可用');
    const data=result.data, items=data.items||[];
    const time=data.updated_at?new Date(data.updated_at).toLocaleString('zh-CN',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'';
    recStatus.textContent=(data.status==='running'?'正在分析最新新闻…':data.status==='error'?`${data.message || '更新失败'}${items.length?'，以下为上次生成的推荐。':''}`:data.status==='ready'?`上次更新 ${time} · 仅供研究，请核实新闻来源`:data.message||'等待首次新闻分析');
    recContent.replaceChildren();
    for(const item of items){
      const card=document.createElement('article');card.className='card recommendation-card';
      const open=button(`在 DSH 对话中使用：${item.title}`,'card-main',()=>{if(launching)return;launching=true;feedback.textContent='正在打开 DSH 对话…';window.parent.postMessage({type:'finfreedom-ask-agent',question:item.markdown},location.origin);setTimeout(()=>{if(launching){launching=false;feedback.textContent='未能打开 DSH 对话，请重试。';}},15000);});
      const title=document.createElement('h3');title.textContent=item.title;open.append(title);
      const meta=document.createElement('div');meta.className='card-meta';const source=document.createElement('span');const link=document.createElement('a');link.textContent=item.source.name;link.href=item.source.url;link.target='_blank';link.rel='noopener noreferrer';source.append(link);const edit=button(`编辑并保存：${item.title}`,'icon-button',()=>openEditor({...item,recommendation:true}));edit.textContent='编辑并保存';meta.append(source,edit);card.append(open,meta);recContent.append(card);
    }
  }catch(e){recStatus.textContent=`推荐暂不可用：${e.message}`;}
}
recRefresh.addEventListener('click',async()=>{recRefresh.disabled=true;recStatus.textContent='正在启动新闻分析…';try{const r=await fetch('/finfreedom/api/recommendations',{method:'POST',headers:{'X-Finfreedom-Client':'1'}});if(!r.ok)throw Error('无法启动更新');setTimeout(loadRecommendations,1500);}catch(e){recStatus.textContent=e.message;}finally{setTimeout(()=>{recRefresh.disabled=false;},5000);}});
loadRecommendations();setInterval(loadRecommendations,30000);
