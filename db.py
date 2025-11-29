import os
import sqlite3
from typing import Any, Dict, List, Optional

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'photos.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS photos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT UNIQUE,
  path TEXT,
  lat REAL,
  lng REAL,
  taken_at TEXT
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)

def add_photo(record: Dict[str, Any]):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO photos (filename, path, lat, lng, taken_at) VALUES (?,?,?,?,?)",
            (
                record['filename'],
                record['path'],
                record.get('lat'),
                record.get('lng'),
                record.get('taken_at'),
            ),
        )

def get_photos(only_with_gps: bool = False) -> List[Dict[str, Any]]:
    cleanup_missing_files()  # Auto-cleanup deleted files
    with get_conn() as conn:
        if only_with_gps:
            rows = conn.execute(
                "SELECT filename, path, lat, lng, taken_at FROM photos WHERE lat IS NOT NULL AND lng IS NOT NULL ORDER BY taken_at"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT filename, path, lat, lng, taken_at FROM photos ORDER BY taken_at"
            ).fetchall()
    return [
        {
            'filename': r[0],
            'path': r[1],
            'lat': r[2],
            'lng': r[3],
            'taken_at': r[4],
        }
        for r in rows
    ]

def update_coords(filename: str, lat: float, lng: float):
    with get_conn() as conn:
        conn.execute(
            "UPDATE photos SET lat=?, lng=? WHERE filename=?",
            (lat, lng, filename),
        )

def update_photo_metadata(filename: str, new_filename: str = None, taken_at: str = None):
    """Update photo filename and/or taken_at date."""
    with get_conn() as conn:
        if new_filename and new_filename != filename:
            # Update filename in DB and rename file
            old_path = conn.execute("SELECT path FROM photos WHERE filename=?", (filename,)).fetchone()
            if old_path:
                old_path = old_path[0]
                new_path = os.path.join(os.path.dirname(old_path), new_filename)
                if os.path.exists(old_path) and not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    conn.execute(
                        "UPDATE photos SET filename=?, path=? WHERE filename=?",
                        (new_filename, new_path, filename)
                    )
                    filename = new_filename  # Update for taken_at change below
        
        if taken_at is not None:
            conn.execute(
                "UPDATE photos SET taken_at=? WHERE filename=?",
                (taken_at, filename)
            )

def cleanup_missing_files() -> int:
    """Remove database entries for photos whose files no longer exist. Returns count removed."""
    with get_conn() as conn:
        rows = conn.execute("SELECT filename, path FROM photos").fetchall()
        removed = 0
        for filename, path in rows:
            if path and not os.path.isfile(path):
                conn.execute("DELETE FROM photos WHERE filename = ?", (filename,))
                removed += 1
        conn.commit()
        return removed

def delete_photo(filename: str) -> None:
    """Remove photo from database."""
    with get_conn() as conn:
        conn.execute("DELETE FROM photos WHERE filename = ?", (filename,))
        conn.commit()

def clear_all() -> None:
    """Remove all photos from database."""
    with get_conn() as conn:
        conn.execute("DELETE FROM photos")
        conn.commit()
