"""Unit tests for stash_id_manager module."""
import unittest
import sqlite3
import tempfile
import os
from datetime import datetime


class StashIDManagerTests(unittest.TestCase):
    """Tests for stash ID management functions."""

    def setUp(self):
        """Set up test database."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, 'test.db')
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        # Create required tables
        self.cursor.execute('''
            CREATE TABLE tags (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT,
                created_at DATETIME,
                updated_at DATETIME
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE tag_stash_ids (
                tag_id INTEGER,
                endpoint VARCHAR(255),
                stash_id VARCHAR(36),
                updated_at DATETIME DEFAULT '1970-01-01T00:00:00Z',
                FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        ''')
        self.conn.commit()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        self.temp_dir.cleanup()

    def _import_module(self):
        """Import stash_id_manager module (done here for test isolation)."""
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        import stash_id_manager
        return stash_id_manager

    def test_migrate_existing_tags_with_urls(self):
        """Test migration of tags with StashDB URLs in descriptions."""
        stash_id_manager = self._import_module()

        # Insert tags with StashDB URLs (using valid hex/UUID format)
        self.cursor.execute(
            "INSERT INTO tags (id, name, description) VALUES (?, ?, ?)",
            (1, 'Tag1', 'A nice tag\nhttps://stashdb.org/tags/abc-def-1234')
        )
        self.cursor.execute(
            "INSERT INTO tags (id, name, description) VALUES (?, ?, ?)",
            (2, 'Tag2', 'https://stashdb.org/tags/feed-beef-5678')
        )
        self.conn.commit()

        # Run migration
        endpoint = "https://stashdb.org/graphql"
        stash_id_manager.migrate_existing_tags(self.conn, endpoint)

        # Verify descriptions were cleaned
        self.cursor.execute("SELECT id, description FROM tags ORDER BY id")
        tags = self.cursor.fetchall()

        self.assertEqual(tags[0]['description'], 'A nice tag')
        self.assertEqual(tags[1]['description'], '')

        # Verify stash IDs were inserted
        self.cursor.execute("SELECT tag_id, endpoint, stash_id FROM tag_stash_ids ORDER BY tag_id")
        stash_ids = self.cursor.fetchall()

        self.assertEqual(len(stash_ids), 2)
        self.assertEqual(stash_ids[0]['tag_id'], 1)
        self.assertEqual(stash_ids[0]['stash_id'], 'abc-def-1234')
        self.assertEqual(stash_ids[0]['endpoint'], endpoint)

        self.assertEqual(stash_ids[1]['tag_id'], 2)
        self.assertEqual(stash_ids[1]['stash_id'], 'feed-beef-5678')

    def test_migrate_existing_tags_without_urls(self):
        """Test migration ignores tags without URLs."""
        stash_id_manager = self._import_module()

        # Insert tag without URL
        self.cursor.execute(
            "INSERT INTO tags (id, name, description) VALUES (?, ?, ?)",
            (1, 'Tag1', 'No URL here')
        )
        self.conn.commit()

        # Run migration
        stash_id_manager.migrate_existing_tags(self.conn, "https://stashdb.org/graphql")

        # Verify description unchanged
        self.cursor.execute("SELECT description FROM tags WHERE id = 1")
        description = self.cursor.fetchone()['description']
        self.assertEqual(description, 'No URL here')

        # Verify no stash IDs were inserted
        self.cursor.execute("SELECT COUNT(*) as count FROM tag_stash_ids")
        count = self.cursor.fetchone()['count']
        self.assertEqual(count, 0)

    def test_migrate_preserves_non_stashdb_urls(self):
        """Test migration preserves non-StashDB URLs in descriptions."""
        stash_id_manager = self._import_module()

        # Insert tag with non-StashDB URL
        self.cursor.execute(
            "INSERT INTO tags (id, name, description) VALUES (?, ?, ?)",
            (1, 'Tag1', 'See https://example.com for more')
        )
        self.conn.commit()

        # Run migration
        stash_id_manager.migrate_existing_tags(self.conn, "https://stashdb.org/graphql")

        # Verify description unchanged
        self.cursor.execute("SELECT description FROM tags WHERE id = 1")
        description = self.cursor.fetchone()['description']
        self.assertEqual(description, 'See https://example.com for more')

    def test_insert_tag_stash_ids(self):
        """Test inserting new tag stash IDs."""
        stash_id_manager = self._import_module()

        # Insert a tag
        self.cursor.execute(
            "INSERT INTO tags (id, name) VALUES (?, ?)",
            (1, 'Tag1')
        )
        self.conn.commit()

        # Insert stash IDs
        tag_mappings = [(1, "https://stashdb.org/graphql", "new-stash-id")]
        stash_id_manager.insert_tag_stash_ids(self.conn, tag_mappings)

        # Verify insertion
        self.cursor.execute("SELECT tag_id, endpoint, stash_id FROM tag_stash_ids WHERE tag_id = 1")
        result = self.cursor.fetchone()

        self.assertEqual(result['tag_id'], 1)
        self.assertEqual(result['endpoint'], "https://stashdb.org/graphql")
        self.assertEqual(result['stash_id'], "new-stash-id")

    def test_insert_tag_stash_ids_empty_list(self):
        """Test inserting empty list doesn't create errors."""
        stash_id_manager = self._import_module()

        # Should not raise an error
        stash_id_manager.insert_tag_stash_ids(self.conn, [])

        # Verify nothing was inserted
        self.cursor.execute("SELECT COUNT(*) as count FROM tag_stash_ids")
        count = self.cursor.fetchone()['count']
        self.assertEqual(count, 0)

    def test_get_existing_stash_ids(self):
        """Test retrieving existing stash IDs."""
        stash_id_manager = self._import_module()

        # Insert some stash IDs
        self.cursor.execute(
            "INSERT INTO tag_stash_ids (tag_id, endpoint, stash_id) VALUES (?, ?, ?)",
            (1, 'https://stashdb.org/graphql', 'id-1')
        )
        self.cursor.execute(
            "INSERT INTO tag_stash_ids (tag_id, endpoint, stash_id) VALUES (?, ?, ?)",
            (2, 'https://stashdb.org/graphql', 'id-2')
        )
        self.conn.commit()

        # Retrieve existing IDs
        existing = stash_id_manager.get_existing_stash_ids(self.conn)

        # Verify results
        self.assertEqual(len(existing), 2)
        self.assertIn((1, 'https://stashdb.org/graphql'), existing)
        self.assertIn((2, 'https://stashdb.org/graphql'), existing)

    def test_idempotent_migration(self):
        """Test that running migration twice is idempotent."""
        stash_id_manager = self._import_module()

        # Insert tag with URL (using valid hex format)
        self.cursor.execute(
            "INSERT INTO tags (id, name, description) VALUES (?, ?, ?)",
            (1, 'Tag1', 'Tag\nhttps://stashdb.org/tags/dead-beef-cafe')
        )
        self.conn.commit()

        endpoint = "https://stashdb.org/graphql"

        # Run migration twice
        stash_id_manager.migrate_existing_tags(self.conn, endpoint)
        stash_id_manager.migrate_existing_tags(self.conn, endpoint)

        # Verify only one stash ID entry exists (due to INSERT OR IGNORE)
        self.cursor.execute("SELECT COUNT(*) as count FROM tag_stash_ids WHERE tag_id = 1")
        count = self.cursor.fetchone()['count']
        self.assertEqual(count, 1)


if __name__ == '__main__':
    unittest.main()
