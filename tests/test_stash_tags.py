"""Tests for tag transfer via GraphQL."""
import pytest
import sys
import os
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stash_tags import transfer_tags_graphql
from models import Tag, Config


@pytest.mark.asyncio
async def test_transfer_creates_new_tags():
    """Test that new tags are created with all fields."""
    mock_client = AsyncMock()
    mock_client.find_existing_tags_with_data = AsyncMock(return_value=({}, {}))
    mock_client.create_tags_batch = AsyncMock(return_value={"tag1": "1"})
    mock_client.update_tags_batch = AsyncMock(return_value=0)

    tags = [
        Tag(
            name="tag1",
            description="Test description",
            stash_id="abc123",
            aliases=["alias1", "alias2"]
        )
    ]

    config = MagicMock(spec=Config)

    await transfer_tags_graphql(mock_client, tags, config)

    # Verify create was called with full tag data
    mock_client.create_tags_batch.assert_called_once()
    created_tags = mock_client.create_tags_batch.call_args[0][0]
    assert len(created_tags) == 1
    assert created_tags[0].description == "Test description"
    assert created_tags[0].aliases == ["alias1", "alias2"]


@pytest.mark.asyncio
async def test_transfer_skips_existing_tags_if_in_sync():
    """Test that existing tags are not re-created if in sync."""
    mock_client = AsyncMock()
    tags_by_name = {
        "tag1": {"id": "1", "name": "tag1", "description": "Test", "aliases": [], "stash_ids": []}
    }
    mock_client.find_existing_tags_with_data = AsyncMock(return_value=(tags_by_name, {}))
    mock_client.create_tags_batch = AsyncMock(return_value={})
    mock_client.update_tags_batch = AsyncMock(return_value=0)

    tags = [
        Tag(name="tag1", description="Test", stash_id="abc", aliases=[])
    ]

    config = MagicMock(spec=Config)

    await transfer_tags_graphql(mock_client, tags, config)

    # Should not call create or update for in-sync tags
    mock_client.create_tags_batch.assert_not_called()
    mock_client.update_tags_batch.assert_not_called()


@pytest.mark.asyncio
async def test_transfer_case_insensitive_deduplication():
    """Test that tag matching is case-insensitive."""
    mock_client = AsyncMock()
    tags_by_name = {
        "action": {"id": "1", "name": "Action", "description": "Action desc", "aliases": [], "stash_ids": []}
    }
    mock_client.find_existing_tags_with_data = AsyncMock(return_value=(tags_by_name, {}))
    mock_client.create_tags_batch = AsyncMock(return_value={})
    mock_client.update_tags_batch = AsyncMock(return_value=0)

    tags = [
        Tag(name="Action", description="Action desc", stash_id="abc", aliases=[])
    ]

    config = MagicMock(spec=Config)

    await transfer_tags_graphql(mock_client, tags, config)

    # Should not create because "Action" matches existing "action" (case-insensitive)
    mock_client.create_tags_batch.assert_not_called()


@pytest.mark.asyncio
async def test_transfer_updates_out_of_sync():
    """Test that out-of-sync tags are updated."""
    mock_client = AsyncMock()
    tags_by_name = {
        "tag1": {"id": "1", "name": "tag1", "description": "Old desc", "aliases": ["old"], "stash_ids": []}
    }
    mock_client.find_existing_tags_with_data = AsyncMock(return_value=(tags_by_name, {}))
    mock_client.create_tags_batch = AsyncMock(return_value={})
    mock_client.update_tags_batch = AsyncMock(return_value=1)

    tags = [
        Tag(name="tag1", description="New desc", stash_id="abc", aliases=["new"])
    ]

    config = MagicMock(spec=Config)

    await transfer_tags_graphql(mock_client, tags, config)

    # Should not create, but should update
    mock_client.create_tags_batch.assert_not_called()
    mock_client.update_tags_batch.assert_called_once()


@pytest.mark.asyncio
async def test_transfer_mixed_new_and_existing():
    """Test that only new tags are created when mixed with existing ones."""
    mock_client = AsyncMock()
    tags_by_name = {
        "tag1": {"id": "1", "name": "tag1", "description": "Existing", "aliases": [], "stash_ids": []}
    }
    mock_client.find_existing_tags_with_data = AsyncMock(return_value=(tags_by_name, {}))
    mock_client.create_tags_batch = AsyncMock(return_value={"tag2": "2"})
    mock_client.update_tags_batch = AsyncMock(return_value=0)

    tags = [
        Tag(name="tag1", description="Existing", stash_id="abc", aliases=[]),
        Tag(name="tag2", description="New", stash_id="def", aliases=[])
    ]

    config = MagicMock(spec=Config)

    await transfer_tags_graphql(mock_client, tags, config)

    # Should only create tag2
    mock_client.create_tags_batch.assert_called_once()
    created_tags = mock_client.create_tags_batch.call_args[0][0]
    assert len(created_tags) == 1
    assert created_tags[0].name == "tag2"


@pytest.mark.asyncio
async def test_transfer_no_tags():
    """Test that nothing happens when tag list is empty."""
    mock_client = AsyncMock()
    mock_client.find_existing_tags_with_data = AsyncMock(return_value=({}, {}))
    mock_client.create_tags_batch = AsyncMock(return_value={})
    mock_client.update_tags_batch = AsyncMock(return_value=0)

    config = MagicMock(spec=Config)

    await transfer_tags_graphql(mock_client, [], config)

    # Should call find but not create or update
    mock_client.find_existing_tags_with_data.assert_called_once()
    mock_client.create_tags_batch.assert_not_called()
    mock_client.update_tags_batch.assert_not_called()


@pytest.mark.asyncio
async def test_transfer_skips_tags_with_no_name():
    """Test that tags without names are skipped."""
    mock_client = AsyncMock()
    mock_client.find_existing_tags_with_data = AsyncMock(return_value=({}, {}))
    mock_client.create_tags_batch = AsyncMock(return_value={"valid_tag": "2"})
    mock_client.update_tags_batch = AsyncMock(return_value=0)

    tags = [
        Tag(name="", description="No name", stash_id="abc", aliases=[]),
        Tag(name="valid_tag", description="Valid", stash_id="def", aliases=[])
    ]

    config = MagicMock(spec=Config)

    await transfer_tags_graphql(mock_client, tags, config)

    # Should only create the valid tag
    mock_client.create_tags_batch.assert_called_once()
    created_tags = mock_client.create_tags_batch.call_args[0][0]
    assert len(created_tags) == 1
    assert created_tags[0].name == "valid_tag"
