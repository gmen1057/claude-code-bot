"""
Database connection pool for PostgreSQL
"""

from contextlib import contextmanager
from typing import Any, Dict, Optional

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

from bot.config import DB_CONFIG, DB_POOL_MAX, DB_POOL_MIN, logger

# Global connection pool
_pool: Optional[pool.ThreadedConnectionPool] = None


def init_pool() -> pool.ThreadedConnectionPool:
    """Initialize the connection pool"""
    global _pool
    if _pool is None:
        try:
            _pool = pool.ThreadedConnectionPool(DB_POOL_MIN, DB_POOL_MAX, **DB_CONFIG)
            logger.info(
                f"Database pool initialized (min={DB_POOL_MIN}, max={DB_POOL_MAX})"
            )
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    return _pool


def close_pool():
    """Close the connection pool"""
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None
        logger.info("Database pool closed")


@contextmanager
def get_connection():
    """Get a connection from the pool"""
    global _pool
    if _pool is None:
        init_pool()

    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        _pool.putconn(conn)


@contextmanager
def get_cursor(dict_cursor: bool = False):
    """Get a cursor from a pooled connection"""
    with get_connection() as conn:
        cursor_factory = RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cur
        finally:
            cur.close()


def execute_query(
    query: str, params: tuple = None, fetch: bool = False, dict_cursor: bool = False
) -> Optional[Any]:
    """Execute a query and optionally fetch results"""
    with get_cursor(dict_cursor=dict_cursor) as cur:
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
        return None


def execute_one(
    query: str, params: tuple = None, dict_cursor: bool = True
) -> Optional[Dict]:
    """Execute a query and fetch one result"""
    with get_cursor(dict_cursor=dict_cursor) as cur:
        cur.execute(query, params)
        return cur.fetchone()


def init_database():
    """Initialize database tables"""
    with get_cursor() as cur:
        # Sessions table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                user_id BIGINT PRIMARY KEY,
                conversation_id UUID DEFAULT gen_random_uuid(),
                context JSONB DEFAULT '[]'::jsonb,
                context_summary TEXT,
                working_dir TEXT DEFAULT '/root',
                active_project TEXT,
                important_decisions JSONB DEFAULT '[]'::jsonb,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INT DEFAULT 0
            )
        """
        )

        # Command logs table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS command_logs (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                command TEXT,
                response TEXT,
                execution_time_ms INT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Rate limiting table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rate_limits (
                user_id BIGINT PRIMARY KEY,
                message_count INT DEFAULT 0,
                window_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        logger.info("Database tables initialized")
