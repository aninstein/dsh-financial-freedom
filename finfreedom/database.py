"""finfreedom-owned database connections and schema initialization.

The active connection profile is stored outside the business database so a
user can switch backends without losing the configuration needed to reconnect.
Secrets are kept in a separate owner-only file until the DSH credentials UI is
wired into the installed-version settings extension.
"""

from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor


SCHEMA_VERSION = 2


class _MySQLCompat:
    """Small DB-API bridge for the question-mark SQL used by finfreedom domains."""

    def __init__(self, connection: Any):
        self._connection = connection

    @staticmethod
    def _sql(statement: str) -> str:
        # Project queries use bound values and do not contain literal question
        # marks. Keep the translation deliberately small and auditable.
        return statement.replace("?", "%s")

    def execute(self, statement: str, params: Any = ()):
        with self._connection.cursor() as cursor:
            cursor.execute(self._sql(statement), params)
            return _BufferedCursor(cursor.fetchall(), cursor.rowcount, cursor.lastrowid)

    def executemany(self, statement: str, params: Any):
        with self._connection.cursor() as cursor:
            cursor.executemany(self._sql(statement), params)
            return _BufferedCursor(cursor.fetchall(), cursor.rowcount, cursor.lastrowid)

    def cursor(self):
        return self._connection.cursor()

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()


class _BufferedCursor:
    def __init__(self, rows: list[dict[str, Any]], rowcount: int, lastrowid: int | None):
        self._rows = rows
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def fetchone(self):
        return self._rows.pop(0) if self._rows else None

    def fetchall(self):
        rows, self._rows = self._rows, []
        return rows

    def __iter__(self):
        return iter(self.fetchall())


def data_dir() -> Path:
    value = os.environ.get("FINFREEDOM_DATA_DIR")
    if value:
        path = Path(value).expanduser()
    else:
        dsh_home = Path(os.environ.get("DSH_HOME", "~/.dsh")).expanduser()
        path = dsh_home / "finfreedom"
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path.resolve()


def _profile_path() -> Path:
    return data_dir() / "database.json"


def _secret_path(credential_ref: str) -> Path:
    if not credential_ref or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in credential_ref):
        raise RuntimeError("finfreedom 数据库凭据引用无效")
    return data_dir() / f"database-secret-{credential_ref}"


def active_profile() -> dict[str, Any]:
    path = _profile_path()
    if not path.exists():
        return {"driver": "sqlite", "path": str(data_dir() / "finfreedom.sqlite3"), "version": 1}
    try:
        value = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("finfreedom 数据库连接配置无法读取") from exc
    if not isinstance(value, dict) or value.get("driver") not in {"sqlite", "mysql"}:
        raise RuntimeError("finfreedom 数据库连接配置无效")
    return value


def _atomic_private_write(path: Path, content: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".finfreedom-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def configure_mysql(host: str, port: int, database: str, user: str,
                    password: str, tls: bool = True) -> None:
    """Validate a candidate before atomically making it active."""
    if not host or len(host) > 255 or any(char in host for char in "\r\n/@"):
        raise ValueError("数据库主机名无效")
    if not 1 <= int(port) <= 65535:
        raise ValueError("数据库端口无效")
    for label, item in (("数据库名", database), ("用户名", user)):
        if not item or len(item) > 128 or "\x00" in item:
            raise ValueError(f"{label}无效")
    credential_ref = uuid.uuid4().hex
    candidate = {"driver": "mysql", "host": host, "port": int(port),
                 "database": database, "user": user, "tls": bool(tls),
                 "credential_ref": credential_ref, "version": 1}
    try:
        _check_mysql(candidate, password)
        _initialize_mysql(candidate, password)
        _atomic_private_write(_secret_path(credential_ref), password)
        _atomic_private_write(_profile_path(), json.dumps(candidate, ensure_ascii=False, indent=2))
    except Exception:
        # A versioned credential file leaves the previous profile usable if
        # the final profile-file replacement fails.
        _secret_path(credential_ref).unlink(missing_ok=True)
        raise


def use_sqlite() -> None:
    """Switch to the local default without deleting an external database."""
    path = data_dir() / "finfreedom.sqlite3"
    connection = sqlite3.connect(path, timeout=10, isolation_level="DEFERRED")
    try:
        _initialize_sqlite(connection)
    finally:
        connection.close()
    profile = {"driver": "sqlite", "path": str(path), "version": 1}
    _atomic_private_write(_profile_path(), json.dumps(profile, ensure_ascii=False, indent=2))


def _mysql_connection(profile: dict[str, Any], password: str):
    ssl = {"check_hostname": True} if profile.get("tls", True) else None
    return pymysql.connect(
        host=profile["host"], port=int(profile["port"]), user=profile["user"],
        password=password, database=profile["database"], charset="utf8mb4",
        cursorclass=DictCursor, autocommit=False, connect_timeout=5,
        read_timeout=15, write_timeout=15, ssl=ssl,
    )


def _check_mysql(profile: dict[str, Any], password: str) -> None:
    raw_connection = _mysql_connection(profile, password)
    connection = _MySQLCompat(raw_connection)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            if not cursor.fetchone():
                raise RuntimeError("数据库连接测试未返回结果")
    finally:
        connection.close()


def _initialize_mysql(profile: dict[str, Any], password: str) -> None:
    connection = _MySQLCompat(_mysql_connection(profile, password))
    try:
        with connection.cursor() as cursor:
            cursor.execute("""CREATE TABLE IF NOT EXISTS finfreedom_schema_version (
                version INT NOT NULL PRIMARY KEY, applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS personal_portfolios (
                owner_id VARCHAR(64) NOT NULL, currency VARCHAR(3) NOT NULL,
                principal DECIMAL(20,2) NULL, cash DECIMAL(20,2) NULL,
                updated_at VARCHAR(40) NOT NULL, PRIMARY KEY(owner_id,currency)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS personal_positions (
                owner_id VARCHAR(64) NOT NULL, currency VARCHAR(3) NOT NULL,
                instrument_id VARCHAR(64) NOT NULL, name VARCHAR(80) NOT NULL,
                asset_class VARCHAR(8) NOT NULL, quantity DOUBLE NULL,
                cost_basis DECIMAL(20,2) NULL, manual_value DECIMAL(20,2) NULL,
                updated_at VARCHAR(40) NOT NULL, reported_return_pct DOUBLE NULL,
                PRIMARY KEY(owner_id,currency,instrument_id),
                INDEX idx_personal_positions_owner(owner_id,currency)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS holdings_history (
                owner_id VARCHAR(64) NOT NULL, currency VARCHAR(3) NOT NULL,
                observed_at VARCHAR(40) NOT NULL, positions_json TEXT NOT NULL,
                PRIMARY KEY(owner_id,currency,observed_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS holdings_import_drafts (
                draft_id VARCHAR(32) NOT NULL PRIMARY KEY, owner_id VARCHAR(64) NOT NULL,
                session_id VARCHAR(128) NULL, currency VARCHAR(3) NOT NULL,
                payload JSON NOT NULL, created_at VARCHAR(40) NOT NULL,
                INDEX idx_holdings_import_drafts_owner(owner_id,session_id,created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS quotes (
                instrument_id VARCHAR(64) NOT NULL PRIMARY KEY, symbol VARCHAR(32) NOT NULL,
                name VARCHAR(128) NOT NULL, market VARCHAR(16) NOT NULL, asset_class VARCHAR(24) NOT NULL,
                last DOUBLE NOT NULL, currency VARCHAR(8) NOT NULL, quote_kind VARCHAR(24) NOT NULL,
                price_unit VARCHAR(32) NOT NULL, exchange_time VARCHAR(40) NULL, received_at VARCHAR(40) NOT NULL,
                provider VARCHAR(128) NOT NULL, freshness VARCHAR(24) NOT NULL,
                known_delay_seconds INT NULL, change_percent DOUBLE NULL, volume DOUBLE NULL,
                INDEX idx_quotes_market(market,symbol), INDEX idx_quotes_received(received_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS watchlist (
                instrument_id VARCHAR(64) NOT NULL PRIMARY KEY, added_at VARCHAR(40) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS bars (
                instrument_id VARCHAR(64) NOT NULL, interval_name VARCHAR(12) NOT NULL,
                bar_time VARCHAR(32) NOT NULL, open DOUBLE NULL, high DOUBLE NULL, low DOUBLE NULL,
                close DOUBLE NULL, volume DOUBLE NULL, currency VARCHAR(8) NOT NULL,
                adjustment VARCHAR(24) NOT NULL, provider VARCHAR(128) NOT NULL, received_at VARCHAR(40) NOT NULL,
                price_unit VARCHAR(32) NOT NULL DEFAULT 'per_share', volume_unit VARCHAR(32) NOT NULL DEFAULT 'unknown',
                PRIMARY KEY(instrument_id,interval_name,bar_time,adjustment),
                INDEX idx_bars_query(instrument_id,interval_name,bar_time)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS dataset_manifests (
                dataset_version VARCHAR(64) NOT NULL PRIMARY KEY, instrument_id VARCHAR(64) NOT NULL,
                interval_name VARCHAR(12) NOT NULL, adjustment VARCHAR(24) NOT NULL,
                provider VARCHAR(128) NOT NULL, start_date VARCHAR(32) NOT NULL, end_date VARCHAR(32) NOT NULL,
                row_count INT NOT NULL, content_hash VARCHAR(128) NOT NULL, ingested_at VARCHAR(40) NOT NULL,
                INDEX idx_dataset_instrument(instrument_id,ingested_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS provider_health (
                market VARCHAR(16) NOT NULL PRIMARY KEY, failure_count INT NOT NULL DEFAULT 0,
                last_attempt_at VARCHAR(40) NULL, next_retry_at VARCHAR(40) NULL,
                last_success_at VARCHAR(40) NULL, last_error TEXT NULL, updated_at VARCHAR(40) NOT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS owner_workspace_state (
                owner_id VARCHAR(64) NOT NULL, kind VARCHAR(32) NOT NULL,payload LONGTEXT NOT NULL,
                version INTEGER NOT NULL,updated_at VARCHAR(40) NOT NULL,PRIMARY KEY(owner_id,kind)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS workspace_cache (
                cache_key VARCHAR(255) NOT NULL PRIMARY KEY, payload LONGTEXT NULL,
                updated_at VARCHAR(40) NOT NULL, last_error TEXT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS ai_documents (
                document_id VARCHAR(64) NOT NULL PRIMARY KEY, filename VARCHAR(255) NOT NULL,
                document_type VARCHAR(40) NOT NULL, instrument_id VARCHAR(64) NULL,
                owner_id VARCHAR(64) NOT NULL, report_period VARCHAR(40) NULL, content_hash VARCHAR(128) NOT NULL,
                page_count INT NOT NULL, imported_at VARCHAR(40) NOT NULL, original_content LONGBLOB NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS ai_document_pages (
                document_id VARCHAR(64) NOT NULL, page_no INT NOT NULL, content LONGTEXT NOT NULL,
                PRIMARY KEY(document_id,page_no), INDEX idx_ai_document_pages_document(document_id,page_no)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS ai_research_runs (
                run_id VARCHAR(64) NOT NULL PRIMARY KEY, owner_id VARCHAR(64) NOT NULL,
                question TEXT NOT NULL, status VARCHAR(24) NOT NULL, model VARCHAR(128) NULL,
                tool_calls INT NOT NULL DEFAULT 0, evidence_json LONGTEXT NOT NULL,
                answer LONGTEXT NULL, error TEXT NULL, created_at VARCHAR(40) NOT NULL,
                completed_at VARCHAR(40) NULL, INDEX idx_ai_research_owner(owner_id,created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("""CREATE TABLE IF NOT EXISTS research_runs (
                run_id VARCHAR(64) NOT NULL PRIMARY KEY, owner_id VARCHAR(64) NOT NULL,
                strategy_id VARCHAR(64) NOT NULL, strategy_version VARCHAR(64) NOT NULL,
                instrument_id VARCHAR(64) NOT NULL, dataset_version VARCHAR(64) NOT NULL,
                parameters LONGTEXT NOT NULL, metrics LONGTEXT NOT NULL, created_at VARCHAR(40) NOT NULL,
                INDEX idx_research_runs_owner(owner_id,created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
            cursor.execute("INSERT IGNORE INTO finfreedom_schema_version(version) VALUES (%s)", (SCHEMA_VERSION,))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _initialize_sqlite(connection: sqlite3.Connection) -> None:
    connection.executescript("""
    CREATE TABLE IF NOT EXISTS owner_workspace_state (
        owner_id TEXT NOT NULL,kind TEXT NOT NULL,payload TEXT NOT NULL,version INTEGER NOT NULL,updated_at TEXT NOT NULL,
        PRIMARY KEY(owner_id,kind)
    );
    CREATE TABLE IF NOT EXISTS research_news (
        news_id TEXT PRIMARY KEY,source TEXT NOT NULL,title TEXT NOT NULL,content TEXT NOT NULL,
        published_at TEXT,url TEXT,first_seen_at TEXT NOT NULL,last_seen_at TEXT NOT NULL,
        content_hash TEXT NOT NULL,associations_json TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_news_published ON research_news(published_at);
    CREATE TABLE IF NOT EXISTS sector_rotation_snapshots (
        observed_date TEXT PRIMARY KEY,received_at TEXT NOT NULL,payload TEXT NOT NULL,sample_hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS finfreedom_schema_version (
        version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS personal_portfolios (
        owner_id TEXT NOT NULL, currency TEXT NOT NULL, principal REAL, cash REAL,
        updated_at TEXT NOT NULL, PRIMARY KEY(owner_id,currency)
    );
    CREATE TABLE IF NOT EXISTS personal_positions (
        owner_id TEXT NOT NULL, currency TEXT NOT NULL, instrument_id TEXT NOT NULL,
        name TEXT NOT NULL, asset_class TEXT NOT NULL, quantity REAL,
        cost_basis REAL, manual_value REAL, updated_at TEXT NOT NULL,
        reported_return_pct REAL, PRIMARY KEY(owner_id,currency,instrument_id)
    );
    CREATE INDEX IF NOT EXISTS idx_personal_positions_owner ON personal_positions(owner_id,currency);
    CREATE TABLE IF NOT EXISTS holdings_history (
        owner_id TEXT NOT NULL, currency TEXT NOT NULL, observed_at TEXT NOT NULL,
        positions_json TEXT NOT NULL, PRIMARY KEY(owner_id,currency,observed_at)
    );
    CREATE TABLE IF NOT EXISTS holdings_import_drafts (
        draft_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, session_id TEXT,
        currency TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_holdings_import_drafts_owner ON holdings_import_drafts(owner_id,session_id,created_at);
    CREATE TABLE IF NOT EXISTS quotes (
        instrument_id TEXT PRIMARY KEY, symbol TEXT NOT NULL, name TEXT NOT NULL,
        market TEXT NOT NULL, asset_class TEXT NOT NULL, last REAL NOT NULL,
        currency TEXT NOT NULL, quote_kind TEXT NOT NULL, price_unit TEXT NOT NULL,
        exchange_time TEXT, received_at TEXT NOT NULL, provider TEXT NOT NULL, freshness TEXT NOT NULL,
        known_delay_seconds INTEGER, change_percent REAL, volume REAL
    );
    CREATE INDEX IF NOT EXISTS idx_quotes_market ON quotes(market,symbol);
    CREATE INDEX IF NOT EXISTS idx_quotes_received ON quotes(received_at);
    CREATE TABLE IF NOT EXISTS watchlist (instrument_id TEXT PRIMARY KEY, added_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS bars (
        instrument_id TEXT NOT NULL, interval_name TEXT NOT NULL, bar_time TEXT NOT NULL,
        open REAL, high REAL, low REAL, close REAL, volume REAL, currency TEXT NOT NULL,
        adjustment TEXT NOT NULL, provider TEXT NOT NULL, received_at TEXT NOT NULL,
        price_unit TEXT NOT NULL DEFAULT 'per_share', volume_unit TEXT NOT NULL DEFAULT 'unknown',
        PRIMARY KEY(instrument_id,interval_name,bar_time,adjustment)
    );
    CREATE INDEX IF NOT EXISTS idx_bars_query ON bars(instrument_id,interval_name,bar_time);
    CREATE TABLE IF NOT EXISTS dataset_manifests (
        dataset_version TEXT PRIMARY KEY, instrument_id TEXT NOT NULL, interval_name TEXT NOT NULL,
        adjustment TEXT NOT NULL, provider TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
        row_count INTEGER NOT NULL, content_hash TEXT NOT NULL, ingested_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_dataset_instrument ON dataset_manifests(instrument_id,ingested_at);
    CREATE TABLE IF NOT EXISTS provider_health (
        market TEXT PRIMARY KEY, failure_count INTEGER NOT NULL DEFAULT 0,
        last_attempt_at TEXT, next_retry_at TEXT, last_success_at TEXT, last_error TEXT, updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS workspace_cache (
        cache_key TEXT PRIMARY KEY, payload TEXT, updated_at TEXT NOT NULL, last_error TEXT
    );
    CREATE TABLE IF NOT EXISTS ai_documents (
        document_id TEXT PRIMARY KEY, filename TEXT NOT NULL, document_type TEXT NOT NULL,
        instrument_id TEXT, owner_id TEXT NOT NULL, report_period TEXT, content_hash TEXT NOT NULL, page_count INTEGER NOT NULL,
        imported_at TEXT NOT NULL, original_content BLOB
    );
    CREATE TABLE IF NOT EXISTS ai_document_pages (
        document_id TEXT NOT NULL, page_no INTEGER NOT NULL, content TEXT NOT NULL,
        PRIMARY KEY(document_id,page_no)
    );
    CREATE INDEX IF NOT EXISTS idx_ai_document_pages_document ON ai_document_pages(document_id,page_no);
    CREATE TABLE IF NOT EXISTS ai_research_runs (
        run_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, question TEXT NOT NULL, status TEXT NOT NULL,
        model TEXT, tool_calls INTEGER NOT NULL DEFAULT 0, evidence_json TEXT NOT NULL DEFAULT '[]',
        answer TEXT, error TEXT, created_at TEXT NOT NULL, completed_at TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_ai_research_owner ON ai_research_runs(owner_id,created_at);
    CREATE TABLE IF NOT EXISTS research_runs (
        run_id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, strategy_id TEXT NOT NULL,
        strategy_version TEXT NOT NULL, instrument_id TEXT NOT NULL, dataset_version TEXT NOT NULL,
        parameters TEXT NOT NULL, metrics TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_research_runs_owner ON research_runs(owner_id,created_at);
    """)
    connection.execute("INSERT OR IGNORE INTO finfreedom_schema_version(version) VALUES (?)", (SCHEMA_VERSION,))
    connection.commit()


@contextmanager
def connect() -> Iterator[Any]:
    profile = active_profile()
    if profile["driver"] == "sqlite":
        path = Path(profile.get("path") or data_dir() / "finfreedom.sqlite3").expanduser()
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        connection = sqlite3.connect(path, timeout=10, isolation_level="DEFERRED")
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=10000")
        connection.execute("PRAGMA journal_mode=WAL")
        _initialize_sqlite(connection)
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        return

    try:
        password = _secret_path(str(profile.get("credential_ref", ""))).read_text("utf-8")
    except OSError as exc:
        raise RuntimeError("finfreedom 数据库凭据未配置，请运行 finfreedom db configure-mysql") from exc
    connection = _MySQLCompat(_mysql_connection(profile, password))
    try:
        connection.execute("""CREATE TABLE IF NOT EXISTS holdings_history (
            owner_id VARCHAR(64) NOT NULL, currency VARCHAR(3) NOT NULL,
            observed_at VARCHAR(40) NOT NULL, positions_json TEXT NOT NULL,
            PRIMARY KEY(owner_id,currency,observed_at)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def status() -> dict[str, Any]:
    profile = active_profile()
    if profile["driver"] == "sqlite":
        path = Path(profile.get("path") or data_dir() / "finfreedom.sqlite3").expanduser()
        try:
            with connect() as db:
                db.execute("SELECT 1").fetchone()
            return {"driver": "sqlite", "endpoint": str(path), "status": "connected",
                    "schema_version": SCHEMA_VERSION}
        except Exception as exc:
            return {"driver": "sqlite", "endpoint": str(path), "status": "error",
                    "error": type(exc).__name__}
    endpoint = f"{profile['host']}:{profile['port']}/{profile['database']}"
    try:
        with connect() as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT 1 AS ok")
        return {"driver": "mysql", "endpoint": endpoint, "status": "connected",
                "schema_version": SCHEMA_VERSION}
    except Exception as exc:
        return {"driver": "mysql", "endpoint": endpoint, "status": "error",
                "error": type(exc).__name__}
