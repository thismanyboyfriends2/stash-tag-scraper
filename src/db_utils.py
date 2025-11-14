"""Database utility functions."""
import sqlite3
from typing import List, Dict


def fetch_tag_ids_by_names(conn: sqlite3.Connection, tag_names: List[str]) -> Dict[str, int]:
    """Batch fetch tag IDs by names."""
    if not tag_names:
        return {}

    cur = conn.cursor()
    placeholders = ",".join("?" for _ in tag_names)
    query = f"SELECT id, name FROM tags WHERE name IN ({placeholders})"
    cur.execute(query, tag_names)

    return {row['name']: row['id'] for row in cur.fetchall()}
