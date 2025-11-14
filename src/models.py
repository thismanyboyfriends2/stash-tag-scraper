"""Data models for the stash tag scraper."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Tag:
    """Represents a tag from StashDB."""
    name: str
    description: str
    url: str
    aliases: list[str]
    category: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'Tag':
        """Create Tag from dictionary (e.g., from GraphQL response)."""
        aliases = data.get('aliases', '')
        if isinstance(aliases, str):
            aliases = [a.strip() for a in aliases.split(',') if a.strip()]
        elif aliases is None:
            aliases = []

        return cls(
            name=data['name'],
            description=data.get('description', ''),
            url=data.get('url', ''),
            aliases=aliases,
            category=data.get('category')
        )

    def get_description_with_url(self) -> str:
        """Get formatted description with URL appended."""
        if self.description:
            return f"{self.description}\n{self.url}"
        return self.url


@dataclass
class Config:
    """Configuration for the stash tag scraper."""
    stashdb_api_key: str
    stash_db_path: Path

    @classmethod
    def from_env(cls, stash_db_path: Optional[str] = None) -> 'Config':
        """Create Config from environment variables and validate paths."""
        import os

        # Validate API key
        api_key = os.getenv('STASHDB_API_KEY')
        if not api_key:
            raise ValueError(
                "STASHDB_API_KEY environment variable is required.\n"
                "Get your API key from https://stashdb.org/register"
            )

        # Determine database path
        if stash_db_path:
            db_path = Path(stash_db_path)
        else:
            default_path = os.getenv('STASH_DB_PATH', os.path.expanduser('~/.stash/stash-go.sqlite'))
            db_path = Path(default_path)

        # Validate database exists
        if not db_path.exists():
            raise FileNotFoundError(
                f"Stash database not found at: {db_path}\n"
                f"Please specify the correct path using:\n"
                f"  --stash-db /path/to/stash-go.sqlite\n"
                f"or set the STASH_DB_PATH environment variable"
            )

        # Validate it's a file
        if not db_path.is_file():
            raise ValueError(
                f"Stash database path is not a file: {db_path}"
            )


        return cls(
            stashdb_api_key=api_key,
            stash_db_path=db_path,
        )
