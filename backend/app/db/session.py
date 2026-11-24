"""
Database Session and Engine Management for NexusDB
Provides connection pooling for PostgreSQL 16 (owner, reader, writer roles)
with seamless automated fallback to local SQLite engine.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.config import get_settings

settings = get_settings()

_engine_owner: Engine | None = None
_engine_reader: Engine | None = None
_engine_writer: Engine | None = None
_use_sqlite: bool | None = None


def is_postgres_available() -> bool:
    global _use_sqlite
    if _use_sqlite is not None:
        return not _use_sqlite

    try:
        engine = create_engine(settings.database_url_owner, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        _use_sqlite = False
        return True
    except Exception:
        _use_sqlite = True
        return False


def get_sqlite_path() -> Path:
    db_file = settings.sqlite_db_path
    if not db_file.exists():
        from db.seed.generate import generate_database
        generate_database(db_file)
    return db_file


def init_database():
    """Initializes database schema and seed if not present."""
    if is_postgres_available():
        pass
    else:
        get_sqlite_path()


@contextmanager
def get_db_connection(role: str = "nexus_reader") -> Generator[Any, None, None]:
    """
    Context manager yielding a database connection for the requested role:
    'nexus_reader' (read-only), 'nexus_writer' (governed write-backs), or 'nexus_owner' (admin/migrations).
    """
    if is_postgres_available():
        if role == "nexus_writer":
            url = settings.database_url_writer
        elif role == "nexus_owner":
            url = settings.database_url_owner
        else:
            url = settings.database_url_reader

        engine = create_engine(url)
        with engine.connect() as conn:
            yield conn
    else:
        # SQLite connection context with attached schemas (bank, app, audit)
        db_file = get_sqlite_path()
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        try:
            # Attach self as bank, app, audit schemas so schema-qualified SQL works natively
            db_path_str = str(db_file).replace('\\', '/')
            try:
                conn.execute(f"ATTACH '{db_path_str}' AS bank")
            except Exception:
                pass
            try:
                conn.execute(f"ATTACH '{db_path_str}' AS app")
            except Exception:
                pass
            try:
                conn.execute(f"ATTACH '{db_path_str}' AS audit")
            except Exception:
                pass

            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
