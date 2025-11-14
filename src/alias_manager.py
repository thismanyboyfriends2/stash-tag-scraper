"""Module for managing tag aliases."""
import os
import sqlite3
from typing import List, Set, Dict
import logging
import json

from models import Tag, Config

# Get absolute paths for output files
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(current_dir, '..', 'output')
os.makedirs(output_dir, exist_ok=True)


def create_tag_aliases(conn: sqlite3.Connection, tags: List[Tag], config: Config):
    """
    Create aliases for tags, skipping conflicts with existing tag names.
    Logs skipped aliases for manual review.
    """
    from tag_creator import get_existing_tag_names
    from db_utils import fetch_tag_ids_by_names

    # Get existing state
    existing_aliases = get_existing_aliases(conn)
    existing_tag_names = get_existing_tag_names(conn)

    # Batch fetch all tag IDs upfront
    tag_names = [tag.name for tag in tags]
    tag_ids_map = fetch_tag_ids_by_names(conn, tag_names)

    alias_rows = []
    seen_aliases = set(existing_aliases)
    skipped_aliases = []

    for tag in tags:
        tag_id = tag_ids_map.get(tag.name)
        if not tag_id:
            logging.warning(f"Tag '{tag.name}' not found in database, skipping aliases")
            continue

        for alias in tag.aliases:
            if alias in existing_tag_names:
                skipped_aliases.append({
                    "alias": alias,
                    "tag_name": tag.name,
                    "tag_id": tag_id
                })
                logging.info(f"Skipped alias '{alias}' for tag '{tag.name}' - conflicts with existing tag")
                continue

            if alias not in seen_aliases:
                alias_rows.append((tag_id, alias))
                seen_aliases.add(alias)

    if alias_rows:
        with conn:
            conn.executemany("""
                INSERT OR IGNORE INTO tag_aliases (tag_id, alias)
                VALUES (?, ?)
            """, alias_rows)
        logging.info(f"Created {len(alias_rows)} tag aliases")

    if skipped_aliases:
        save_skipped_aliases(conn, skipped_aliases, config)


def save_skipped_aliases(conn: sqlite3.Connection, skipped_aliases: List[Dict], config: Config):
    """Save skipped aliases to JSON file with enriched information."""
    # Enrich with conflicting tag information
    for alias_info in skipped_aliases:
        alias_str = alias_info["alias"]
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM tags WHERE name = ?", (alias_str,))
        row = cur.fetchone()

        if row:
            alias_info["existing_tag_name"] = row["name"]
        else:
            alias_info["existing_tag_name"] = None

    skipped_aliases_path = os.path.join(output_dir, 'skipped_aliases.json')
    with open(skipped_aliases_path, "w", encoding="utf-8") as f:
        json.dump(skipped_aliases, f, indent=2, ensure_ascii=False)

    logging.warning(f"Skipped {len(skipped_aliases)} aliases. See {skipped_aliases_path} for details.")


def get_existing_aliases(conn: sqlite3.Connection) -> Set[str]:
    """Get all existing aliases from the database."""
    cur = conn.cursor()
    cur.execute("SELECT alias FROM tag_aliases")
    return {row['alias'] for row in cur.fetchall()}
