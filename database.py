import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict

from evm_logger import get_logger

log = get_logger("smart_evm.database")

_DB_PATH: Optional[str] = None


def _get_db_path() -> str:
    global _DB_PATH
    if _DB_PATH is None:
        try:
            from kivy.app import App
            app = App.get_running_app()
            if app is not None:
                _DB_PATH = os.path.join(app.user_data_dir, "evm.db")
            else:
                _DB_PATH = os.path.join(os.path.expanduser("~"), "evm.db")
        except Exception:
            _DB_PATH = "evm.db"
    return _DB_PATH


def _connect() -> sqlite3.Connection:
    path = _get_db_path()
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS votes (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp     TEXT    NOT NULL,
                candidate_id  INTEGER NOT NULL,
                candidate_name TEXT   NOT NULL,
                event_type    TEXT    NOT NULL
            )
        """)
        conn.commit()
        log.info("Database initialised at %s", _get_db_path())
    finally:
        conn.close()


def record_vote(candidate_id: int, candidate_name: str, event_type: str = "vote") -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO votes (timestamp, candidate_id, candidate_name, event_type) VALUES (?,?,?,?)",
            (ts, candidate_id, candidate_name, event_type),
        )
        conn.commit()
    finally:
        conn.close()


def get_vote_totals() -> Dict[int, int]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT candidate_id, COUNT(*) as cnt FROM votes WHERE event_type='vote' GROUP BY candidate_id"
        ).fetchall()
        return {r["candidate_id"]: r["cnt"] for r in rows}
    finally:
        conn.close()


def get_all_events(limit: Optional[int] = None) -> List[sqlite3.Row]:
    conn = _connect()
    try:
        q = "SELECT * FROM votes ORDER BY id DESC"
        if limit:
            q += f" LIMIT {limit}"
        return conn.execute(q).fetchall()
    finally:
        conn.close()


def get_total_votes() -> int:
    conn = _connect()
    try:
        row = conn.execute("SELECT COUNT(*) FROM votes WHERE event_type='vote'").fetchone()
        return row[0]
    finally:
        conn.close()


def clear_all() -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM votes")
        conn.commit()
        log.info("All vote records cleared.")
    finally:
        conn.close()
