"""Owner-scoped prompt entries and frozen favorites for the AI research library."""
from __future__ import annotations
import json
import re
import uuid
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
from finfreedom import workspace_state

CATALOG = Path(__file__).with_name('data') / 'guide-entries.json'
ID = re.compile(r'^(?:builtin-[a-zA-Z0-9_-]{1,64}|user-[a-f0-9]{32})$')

def builtin_entries():
    return json.loads(CATALOG.read_text('utf-8'))

def _state(owner):
    return workspace_state.get_state(owner, 'guide')

def _entry(ident, markdown, source, favorite=False, group='个人词条'):
    lines = markdown.splitlines()
    title = next((x[2:].strip() for x in lines if x.startswith('# ') and x[2:].strip()), '未命名词条')[:100]
    return {'id':ident,'title':title,'markdown':markdown,'source':source,'favorite':favorite,'group':group}

def _is_new(row, today=None):
    try:
        added = date.fromisoformat(row.get('added_at', ''))
    except (ValueError, TypeError):
        return False
    today = today or datetime.now(ZoneInfo('Asia/Shanghai')).date()
    return 0 <= (today - added).days < 30

def list_entries(owner, view='favorites'):
    if view not in {'favorites','mine','all'}: raise ValueError('视图仅支持 favorites、mine、all')
    state = _state(owner)
    builtins={x['id']:x for x in builtin_entries()}
    mine=state['mine']; favorites=state['favorites']
    if view == 'favorites':
        entries=[_entry(i, row['markdown'], 'mine' if i in mine or i not in builtins else 'builtin', True, row.get('group','收藏')) for i,row in favorites.items()]
    elif view == 'mine':
        entries=[_entry(i, row['markdown'], 'mine', i in favorites, row.get('group','个人词条')) for i,row in mine.items()]
    else:
        entries=[]
        for ident, row in builtins.items():
            effective = mine.get(ident) or favorites.get(ident) or row
            entries.append(_entry(ident,effective['markdown'],'mine' if ident in mine else 'builtin',ident in favorites,effective.get('group',row.get('group','内置'))))
    for entry in entries:
        builtin = builtins.get(entry['id'], {})
        entry['is_new'] = entry['id'] not in mine and _is_new(builtin)
        entry['skill_origin'] = builtin.get('origin') if entry['id'] not in mine else None
        entry['priority'] = builtin.get('priority', 0) if entry['is_new'] else 0
    entries.sort(key=lambda x: (not x['is_new'], -x['priority'], not x['favorite']))
    return {'view':view,'entries':entries,'version':state['version']}

def manage(owner, action, data):
    if action not in {'create','update','favorite','unfavorite','delete'}: raise ValueError('词条操作无效')
    if not isinstance(data,dict) or not isinstance(data.get('expected_version'),int) or isinstance(data.get('expected_version'),bool): raise ValueError('请先读取词条版本')
    state=_state(owner)
    if data['expected_version'] != state['version']: raise ValueError('词条已更新，请刷新后重试')
    mine=state['mine']; favorites=state['favorites']; builtins={x['id']:x for x in builtin_entries()}
    ident=data.get('id','')
    if action=='create': ident='user-'+uuid.uuid4().hex
    elif not isinstance(ident,str) or not ID.fullmatch(ident): raise ValueError('词条编号无效')
    current=mine.get(ident) or favorites.get(ident) or builtins.get(ident)
    if action != 'create' and current is None: raise ValueError('词条不存在')
    if action in {'create','update'}:
        markdown=data.get('markdown')
        if not isinstance(markdown,str) or not markdown.strip() or len(markdown)>20000: raise ValueError('Markdown 内容不能为空且不能超过 20000 字')
        if not re.search(r'^#\s+\S',markdown,re.MULTILINE): raise ValueError('请用一级标题（# 标题）填写词条名称')
        row={'markdown':markdown,'group':current.get('group','个人词条') if current else '个人词条'}
        mine[ident]=row
        if ident in favorites: favorites[ident]=dict(row)
    elif action=='favorite': favorites[ident]={'markdown':current['markdown'],'group':current.get('group','收藏')}
    elif action=='unfavorite': favorites.pop(ident,None)
    elif action=='delete':
        if ident not in mine: raise ValueError('只能删除自己创建或编辑的词条')
        del mine[ident]
    try:
        saved=workspace_state.put_state(owner,'guide',{'mine':mine,'favorites':favorites},data['expected_version'])
    except workspace_state.HTTPException as exc: raise ValueError(exc.detail) from exc
    return {'id':ident,'version':saved['version'],'action':action}
