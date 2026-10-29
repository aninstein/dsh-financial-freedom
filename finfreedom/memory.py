"""Owner-scoped investment notes shared by the DSH agent and workspace."""
from __future__ import annotations
import hashlib
import re
import secrets
from datetime import datetime, timezone
from finfreedom.database import connect


def init(db):
    db.execute('''CREATE TABLE IF NOT EXISTS finfreedom_memories (
        entry_id VARCHAR(26) PRIMARY KEY, owner_id VARCHAR(64) NOT NULL,
        tier VARCHAR(16) NOT NULL, content TEXT NOT NULL,
        created_at VARCHAR(40) NOT NULL, updated_at VARCHAR(40) NOT NULL)''')


def digest(content): return hashlib.sha256(content.encode('utf-8')).hexdigest()


def entries(owner, query='', limit=30):
    query = str(query).strip()[:120]
    with connect() as db:
        init(db)
        rows=db.execute('SELECT entry_id,tier,content,created_at,updated_at FROM finfreedom_memories WHERE owner_id=? ORDER BY updated_at DESC LIMIT 200',(owner,)).fetchall()
    # Chinese text does not have whitespace word boundaries; match the full query,
    # then individual terms when a multiword query is supplied.
    terms=[x for x in re.split(r'\s+',query.casefold()) if x]
    if terms:
        matching=[r for r in rows if any(t in r['content'].casefold() for t in terms)]
        rows=matching or rows
    return [dict(r) for r in rows[:min(max(int(limit),1),50)]]


def remember(owner, content, tier='long-term'):
    content=str(content).strip()
    if not 1<=len(content)<=12000 or tier not in {'long-term','short-term'}: raise ValueError('记忆内容或分类无效')
    stamp=datetime.now(timezone.utc).isoformat(); identifier='M-'+secrets.token_hex(12)
    with connect() as db:
        init(db)
        existing=db.execute('SELECT entry_id FROM finfreedom_memories WHERE owner_id=? AND tier=? AND content=?',(owner,tier,content)).fetchone()
        if existing: return {'entry_id':existing['entry_id'],'created':False}
        db.execute('INSERT INTO finfreedom_memories(entry_id,owner_id,tier,content,created_at,updated_at) VALUES(?,?,?,?,?,?)',(identifier,owner,tier,content,stamp,stamp))
    return {'entry_id':identifier,'created':True}


def tree(owner, path=''):
    if path not in {'','short-term','long-term','daily','sessions'}: raise ValueError('目录不可用')
    if not path:
        items=[{'name':'index.md','path':'index.md','type':'markdown','kind':'index','editable':False}]
        items += [{'name':x,'path':x,'type':'directory'} for x in ('daily','short-term','long-term','sessions')]
    elif path in {'daily','sessions'}: items=[]
    else:
        items=[{'name':r['entry_id']+'.md','path':path+'/'+r['entry_id']+'.md','type':'markdown','kind':'entry','editable':True} for r in entries(owner,limit=50) if r['tier']==path]
    return {'path':path,'items':items}


def document(owner, path):
    if path=='index.md':
        content='# 投资记忆\n\n这里保存 DSH Agent 和你记录的投资偏好与研究上下文。可进入短期或长期记忆查看和编辑。\n'
        return {'path':path,'name':path,'kind':'index','editable':False,'content':content,'sha256':digest(content)}
    m=re.fullmatch(r'(short-term|long-term)/(M-[a-f0-9]{24})\.md',path)
    if not m: raise ValueError('记忆文档不存在')
    with connect() as db:
        init(db); row=db.execute('SELECT * FROM finfreedom_memories WHERE owner_id=? AND tier=? AND entry_id=?',(owner,m[1],m[2])).fetchone()
    if not row: raise ValueError('记忆文档不存在')
    return {'path':path,'name':m[2]+'.md','kind':'entry','editable':True,'content':row['content'],'sha256':digest(row['content'])}


def save(owner,path,content,expected):
    current=document(owner,path); content=str(content).strip()
    if not current['editable'] or current['sha256']!=expected: raise ValueError('记忆已更新，请刷新后重试')
    if not 1<=len(content)<=12000: raise ValueError('记忆内容长度无效')
    entry_id=current['name'][:-3]; stamp=datetime.now(timezone.utc).isoformat()
    with connect() as db:
        init(db)
        result=db.execute('UPDATE finfreedom_memories SET content=?,updated_at=? WHERE owner_id=? AND entry_id=? AND content=?',(content,stamp,owner,entry_id,current['content']))
        if result.rowcount != 1: raise ValueError('记忆已更新，请刷新后重试')
    return document(owner,path)


def delete(owner,entry_id):
    if not re.fullmatch(r'M-[a-f0-9]{24}',entry_id): raise ValueError('记忆编号无效')
    with connect() as db:
        init(db); result=db.execute('DELETE FROM finfreedom_memories WHERE owner_id=? AND entry_id=?',(owner,entry_id))
    return {'deleted':result.rowcount == 1}
