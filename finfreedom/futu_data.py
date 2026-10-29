"""Read-only OpenD bridge with bounded process lifetime and short-lived cache."""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import tempfile
import re
from pathlib import Path
import time

_lock = threading.Lock()
_key_locks: dict[str, threading.Lock] = {}
_cache: dict[str, tuple[float, dict]] = {}


def _run(kind: str, mode: str = '', force: bool = False) -> dict:
    key = f'{kind}:{mode}'
    with _lock:
        key_lock = _key_locks.setdefault(key, threading.Lock())
    with key_lock:
        old = _cache.get(key)
        ttl = 30 if kind in {'accounts','account_summary','discover_real'} and old and old[1].get('state') in {'connected', 'partial'} else (60 if old and (old[1].get('rows') or old[1].get('indices')) else 5)
        if not force and old and time.monotonic() - old[0] < ttl:
            return old[1]
        if os.getenv('FINFREEDOM_FUTU_ENABLED', 'true').lower() not in {'true','1','yes'}:
            return {'state':'disabled', 'source':'富途 OpenD', 'rows':[], 'accounts':[]}
        names = {'PATH','HOME','LANG','LC_ALL','TZ','FUTU_OPEND_HOST','FUTU_OPEND_PORT',
                 'CONTAINER_RUNTIME','FINFREEDOM_FUTU_REAL_ACCOUNT_IDS'}
        env = {key:value for key,value in os.environ.items() if key in names}
        env['FINFREEDOM_FUTU_REAL_ACCOUNT_TOKENS'] = ','.join(real_access())
        try:
            proc = subprocess.run([sys.executable, '-m', 'finfreedom.futu_worker', kind, mode],
                                  env=env, capture_output=True, text=True, timeout=12, check=True)
            data = json.loads(proc.stdout)
            if not isinstance(data, dict):
                raise ValueError('invalid provider response')
        except (subprocess.SubprocessError, ValueError, OSError):
            data = {'state':'unavailable', 'source':'富途 OpenD', 'rows':[], 'accounts':[],
                    'error':'OpenD 连接失败或请求超时。'}
        if old and kind == 'quotes' and not data.get('rows') and old[1].get('rows'):
            data = {**old[1], 'state':'partial', 'note':'OpenD 暂时不可用或受到限流，显示最近一次成功读取的结果；请查看行情时间。'}
        _cache[key] = (time.monotonic(), data)
        return data


def watchlist() -> dict:
    return _run('quotes')


def account_summary(mode: str) -> dict:
    return _run('account_summary', mode)


def accounts(mode: str) -> dict:
    return _run('accounts', mode)


def port_status() -> dict:
    from finfreedom.providers.futu_provider import address
    try:
        host, port = address()
        with socket.create_connection((host, port), timeout=0.5):
            return {'host':host, 'port':port, 'reachable':True}
    except (OSError, ValueError):
        return {'host':'127.0.0.1', 'port':11111, 'reachable':False}


def _access_path() -> Path:
    from finfreedom.database import data_dir
    return data_dir() / 'futu-real-read-access.json'


def real_access() -> list[str]:
    try:
        value = json.loads(_access_path().read_text('utf-8'))
        if isinstance(value, list):
            return [x for x in value if isinstance(x,str) and re.fullmatch(r'futu-real-(?:hk|us)-[a-f0-9]{24}',x)]
    except (OSError, ValueError):
        pass
    return []


def discover_real(force: bool = False) -> dict:
    return _run('discover_real', 'REAL', force=force)


def set_real_access(selected: list[str]) -> dict:
    if not isinstance(selected,list) or len(selected)>30 or len(selected)!=len(set(selected)):
        raise ValueError('账户选择无效')
    discovered=discover_real()
    if discovered.get('state') != 'connected':
        raise ValueError('账户列表未完整读取，请检查 OpenD 后刷新')
    available={a['id'] for a in discovered.get('accounts',[])}
    if not set(selected).issubset(available): raise ValueError('账户列表已变化，请刷新后重试')
    keys = ('account_summary:REAL','accounts:REAL','discover_real:REAL')
    with _lock:
        locks = [_key_locks.setdefault(key, threading.Lock()) for key in keys]
    for lock in locks: lock.acquire()
    try:
        path=_access_path()
        fd, tmp=tempfile.mkstemp(prefix='.futu-access-',dir=path.parent)
        try:
            os.fchmod(fd,0o600)
            with os.fdopen(fd,'w',encoding='utf-8') as stream: json.dump(selected,stream)
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
        for key in keys: _cache.pop(key,None)
    finally:
        for lock in reversed(locks): lock.release()
    return {'saved':True,'count':len(selected)}
