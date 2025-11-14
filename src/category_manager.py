"""Module for managing tag categories and relationships."""
import sqlite3
from typing import List, Dict, Optional
import logging

from models import Tag
from db_utils import fetch_tag_ids_by_names


def categorise_tags(conn: sqlite3.Connection, tags: List[Tag]):
    """Create parent-child relationships between tags and their categories."""
    category_tags = get_category_tags(conn)

    # Batch fetch all tag IDs upfront
    tag_names = [tag.name for tag in tags if tag.category]
    tag_ids_map = fetch_tag_ids_by_names(conn, tag_names)

    relation_rows = []
    skipped_count = 0

    for tag in tags:
        if not tag.category:
            logging.debug(f"No category found for '{tag.name}'. Skipping.")
            skipped_count += 1
            continue

        category = normalise_category(tag.category)
        parent_id = category_tags.get(category)

        if not parent_id:
            logging.debug(f"Category '{category}' not found in target DB ({tag.name}). Skipping.")
            continue

        child_id = tag_ids_map.get(tag.name)
        if not child_id:
            logging.debug(f"Tag '{tag.name}' not found in target DB. Skipping.")
            skipped_count += 1
            continue

        relation_rows.append((parent_id, child_id))

    if relation_rows:
        with conn:
            cur = conn.cursor()
            cur.executemany("""
                INSERT OR IGNORE INTO tags_relations (parent_id, child_id)
                VALUES (?, ?)
            """, relation_rows)
        logging.info(f"Added {len(relation_rows)} category relations, skipped {skipped_count} tags")


def get_category_tags(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get mapping of category tag names to IDs."""
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM tags WHERE name LIKE 'category:%';")
    return {row['name']: row['id'] for row in cur.fetchall()}


def normalise_category(raw_category: Optional[str]) -> Optional[str]:
    """Normalize category name to match Stash format."""
    if not raw_category:
        return None
    lower_no_spaces = raw_category.lower().replace(" ", "")
    return f"category:{lower_no_spaces}"
