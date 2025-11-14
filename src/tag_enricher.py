"""Module for enriching tags with additional information."""
import sqlite3
from datetime import datetime
from typing import List, Dict
import logging

from models import Tag


def enrich_tags_with_information(conn: sqlite3.Connection, tags_by_name: Dict[str, Tag]):
    """Update descriptions for recently created tags."""
    tags_to_enrich = fetch_tags_for_enrichment(conn, '-1 hour')

    now = datetime.now().isoformat(' ')
    update_data = []

    for tag in tags_to_enrich:
        scraped_tag = tags_by_name.get(tag["name"])
        if scraped_tag:
            update_data.append((scraped_tag.get_description_with_url(), now, tag["id"]))

    if update_data:
        with conn:
            cur = conn.cursor()
            cur.executemany("""
                UPDATE tags SET description = ?, updated_at = ? WHERE id = ?
            """, update_data)
        logging.info(f"Enriched {len(update_data)} tags with descriptions")


def fetch_tags_for_enrichment(conn: sqlite3.Connection, time_interval: str = '-1 hour') -> List[Dict]:
    """Fetch tags that need enrichment based on update time."""
    cur = conn.cursor()
    query = """
        SELECT id, name, created_at, updated_at, description, ignore_auto_tag, favorite, sort_name
        FROM tags
        WHERE updated_at <= datetime('now', ?)
    """
    cur.execute(query, (time_interval,))
    return [dict(row) for row in cur.fetchall()]
