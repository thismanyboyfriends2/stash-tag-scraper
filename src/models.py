"""Data models for the stash tag scraper."""
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse


@dataclass
class Tag:
    """Represents a tag from StashDB."""
    name: str
    description: str
    stash_id: str
    aliases: list[str]
    category: Optional[str] = None
    url: Optional[str] = None  # For internal use during scraping

    @classmethod
    def from_dict(cls, data: dict) -> 'Tag':
        """Create Tag from dictionary."""
        aliases = data.get('aliases', '')

        # Normalise aliases to list of strings
        if isinstance(aliases, str):
            aliases = [a.strip() for a in aliases.split(',') if a.strip()]
        elif isinstance(aliases, list):
            # Filter to strings only, strip whitespace
            aliases = [str(a).strip() for a in aliases if a and str(a).strip()]
        elif aliases is None:
            aliases = []
        else:
            # Invalid type, treat as empty
            aliases = []

        return cls(
            name=data['name'],
            description=data.get('description', ''),
            stash_id=data.get('stash_id', ''),
            url=data.get('url'),
            aliases=aliases,
            category=data.get('category')
        )


@dataclass
class StashConnection:
    """Configuration for connecting to a local Stash instance via GraphQL."""
    scheme: str = "http"
    host: str = "localhost"
    port: int = 9999
    api_key: Optional[str] = None

    def to_connection_dict(self) -> dict:
        """Convert to connection dictionary."""
        conn = {
            "Scheme": self.scheme,
            "Host": self.host,
            "Port": self.port,
        }
        if self.api_key:
            conn["ApiKey"] = self.api_key
        return conn

    @classmethod
    def from_env(cls) -> 'StashConnection':
        """Create StashConnection from STASH_ENDPOINT env var."""
        import os

        endpoint = os.getenv('STASH_ENDPOINT', 'http://localhost:9999')
        parsed = urlparse(endpoint)
        return cls(
            scheme=parsed.scheme or 'http',
            host=parsed.hostname or 'localhost',
            port=parsed.port or 9999,
            api_key=os.getenv('STASH_API_KEY'),
        )


@dataclass
class Config:
    """Configuration for the stash tag scraper."""
    stashdb_api_key: str
    ignored_aliases: list[str] = None  # Aliases to skip during merge

    def __post_init__(self):
        """Initialise ignored_aliases if not provided."""
        if self.ignored_aliases is None:
            self.ignored_aliases = []

    @classmethod
    def from_env(cls) -> 'Config':
        """Create Config from STASHDB_API_KEY environment variable and load ignored aliases from file."""
        import os
        from pathlib import Path

        api_key = os.getenv('STASHDB_API_KEY')
        if not api_key:
            raise ValueError(
                "STASHDB_API_KEY environment variable is required.\n"
                "Get your API key from https://stashdb.org/register"
            )

        # Load ignored aliases from .ignored_aliases file if it exists
        ignored_aliases = []
        ignored_file = Path.cwd() / '.ignored_aliases'
        if ignored_file.exists():
            with open(ignored_file, 'r') as f:
                ignored_aliases = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        return cls(stashdb_api_key=api_key, ignored_aliases=ignored_aliases)
