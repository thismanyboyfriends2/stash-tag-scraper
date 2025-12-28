"""Module for enriching tags with additional information."""
import sqlite3
from datetime import datetime
from typing import List, Dict
import logging

from models import Tag
from stash_id_manager import insert_tag_stash_ids


def enrich_tags_with_information(conn: sqlite3.Connection, tags_by_name: Dict[str, Tag], endpoint: str):
    """Update descriptions for recently created tags and insert stash IDs."""
    tags_to_enrich = fetch_tags_for_enrichment(conn, '-1 hour')

    now = datetime.now().isoformat(' ')
    update_data = []
    stash_id_mappings = []

    for tag in tags_to_enrich:
        scraped_tag = tags_by_name.get(tag["name"])
        if scraped_tag:
            # Update description with just the description (no URL)
            update_data.append((scraped_tag.description, now, tag["id"]))

            # Prepare stash ID mapping
            stash_id_mappings.append((tag["id"], endpoint, scraped_tag.stash_id))

    if update_data:
        with conn:
            cur = conn.cursor()
            cur.executemany("""
                UPDATE tags SET description = ?, updated_at = ? WHERE id = ?
            """, update_data)
        logging.info(f"Enriched {len(update_data)} tags with descriptions")

    # Insert stash ID mappings for enriched tags
    if stash_id_mappings:
        insert_tag_stash_ids(conn, stash_id_mappings, updated_at=now)


def fetch_tags_for_enrichment(conn: sqlite3.Connection, time_interval: str = '-1 hour') -> List[Dict]:
    """Fetch tags that need enrichment based on update time."""
    cur = conn.cursor()
    query = """
        SELECT id, name, created_at, updated_at, description, ignore_auto_tag, favorite, sort_name
        FROM tags
        WHERE updated_at >= datetime('now', ?)
    """
    cur.execute(query, (time_interval,))
    return [dict(row) for row in cur.fetchall()]
