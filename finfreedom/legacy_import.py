"""Import selected legacy data into an empty or existing local SQLite store.

The source runs a read-only snapshot inside the existing Financial Freedom
container. Neither credentials nor records are printed to the terminal.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from finfreedom.database import active_profile, connect, data_dir
from finfreedom.mcp_server import _owner

_EXPORT = r'''
import json
from app.mysql_db import connect
tables = ['watchlist', 'quotes', 'bars', 'personal_portfolios', 'personal_positions', 'workspace_cache', 'research_news']
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    db.execute('START TRANSACTION WITH CONSISTENT SNAPSHOT')
    owners = db.execute('SELECT owner_id FROM personal_portfolios UNION SELECT owner_id FROM personal_positions').fetchall()
    print(json.dumps({'kind':'owners','count':len(owners)}), flush=True)
    if len(owners) > 1:
        raise SystemExit('multiple legacy owners')
    for table in tables:
        query = 'SELECT * FROM `' + table + '`'
        if table == 'workspace_cache':
            query += " WHERE cache_key LIKE 'research:%' OR cache_key LIKE 'funds:%' OR cache_key LIKE 'sector:%' OR cache_key LIKE 'flows:%' OR cache_key LIKE 'dossier:%'"
        for row in db.execute(query):
            print(json.dumps({'kind':'row','table':table,'row':dict(row)}, ensure_ascii=False, default=str, allow_nan=False), flush=False)
'''

_COLUMNS = {
    'workspace_cache': ('cache_key','payload','updated_at','last_error'),
    'research_news': ('news_id','source','title','content','published_at','url','first_seen_at','last_seen_at','content_hash','associations_json'),
    'watchlist': ('instrument_id','added_at'),
    'quotes': ('instrument_id','symbol','name','market','asset_class','last','currency',
               'quote_kind','price_unit','exchange_time','received_at','provider','freshness',
               'known_delay_seconds','change_percent','volume'),
    'bars': ('instrument_id','interval_name','bar_time','open','high','low','close','volume',
             'currency','adjustment','provider','received_at','price_unit','volume_unit'),
    'personal_portfolios': ('owner_id','currency','principal','cash','updated_at'),
    'personal_positions': ('owner_id','currency','instrument_id','name','asset_class','quantity',
                           'cost_basis','manual_value','updated_at','reported_return_pct'),
}


def import_from_container(container: str) -> dict:
    if not container or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-' for c in container):
        raise ValueError('容器名称无效')
    profile = active_profile()
    if profile['driver'] != 'sqlite':
        raise RuntimeError('当前导入工具仅支持目标 SQLite；外部数据库需要先完成备份与兼容适配。')
    # Initialize the target first, then take a consistent SQLite backup.
    with connect():
        pass
    path = Path(profile.get('path') or data_dir() / 'finfreedom.sqlite3').expanduser()
    backup_dir = data_dir() / 'backups'
    backup_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup = backup_dir / ('before-legacy-import-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.sqlite3')
    fd = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    source_db = sqlite3.connect(path)
    backup_db = sqlite3.connect(backup)
    try:
        source_db.backup(backup_db)
    finally:
        backup_db.close()
        source_db.close()

    proc = subprocess.Popen(['docker', 'exec', container, 'python', '-c', _EXPORT],
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding='utf-8')
    counts = {name: {'imported': 0, 'skipped': 0} for name in _COLUMNS}
    seen_header = False
    target_owner = _owner()
    try:
        with connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS research_news (
                news_id TEXT PRIMARY KEY, source TEXT NOT NULL, title TEXT NOT NULL, content TEXT NOT NULL,
                published_at TEXT, url TEXT, first_seen_at TEXT NOT NULL, last_seen_at TEXT NOT NULL,
                content_hash TEXT NOT NULL, associations_json TEXT NOT NULL)''')
            for line in proc.stdout:
                item = json.loads(line)
                if item.get('kind') == 'owners':
                    if item.get('count', 0) > 1:
                        raise RuntimeError('旧库有多个持仓归属，无法自动映射到本机用户。')
                    seen_header = True
                    continue
                if not seen_header or item.get('kind') != 'row' or item.get('table') not in _COLUMNS:
                    raise RuntimeError('旧数据导出格式无效')
                table = item['table']
                row = item['row']
                if table.startswith('personal_'):
                    row['owner_id'] = target_owner
                if table == 'quotes':
                    # The source is a historical cache, never assert that it is live.
                    row['freshness'] = 'stale'
                if table == 'bars':
                    row['interval_name'] = row.pop('interval', None)
                cols = _COLUMNS[table]
                before = db.total_changes
                db.execute(f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})",
                           tuple(row.get(col) for col in cols))
                counts[table]['imported' if db.total_changes > before else 'skipped'] += 1
            if proc.wait() != 0 or not seen_header:
                raise RuntimeError('旧数据库读取失败，导入事务已回滚。')
    except BaseException:
        proc.kill()
        proc.wait()
        raise
    finally:
        if proc.stdout:
            proc.stdout.close()
    return {'backup': str(backup), 'counts': counts}
