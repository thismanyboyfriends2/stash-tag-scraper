"""
GraphQL client for StashDB API.
Fetches tag information directly from the StashDB.org GraphQL endpoint.
"""
import logging
import requests
from typing import List, Dict, Optional
from models import Tag


class StashDBClient:
    """Client for interacting with StashDB GraphQL API."""

    def __init__(self, endpoint: str = "https://stashdb.org/graphql", api_key: str = None):
        """
        Initialize StashDB client.

        Args:
            endpoint: GraphQL endpoint URL
            api_key: API key for authentication
        """
        self.endpoint = endpoint
        self.api_key = api_key

        if not self.api_key:
            raise ValueError(
                "StashDB API key is required. "
                "Pass api_key parameter or use Config.from_env()."
            )

        self.headers = {
            'ApiKey': self.api_key,
            'Content-Type': 'application/json'
        }

    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Query response data

        Raises:
            requests.exceptions.RequestException: If request fails
            ValueError: If GraphQL returns errors
        """
        payload = {'query': query}
        if variables:
            payload['variables'] = variables

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            result = response.json()

            if 'errors' in result:
                error_messages = [err.get('message', str(err)) for err in result['errors']]
                raise ValueError(f"GraphQL errors: {', '.join(error_messages)}")

            return result.get('data', {})

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            raise

    def query_all_tags(self) -> List[Tag]:
        """
        Fetch all tags from StashDB using pagination.

        Returns:
            List of Tag objects
        """
        query = """
        query QueryTags($input: TagQueryInput!) {
            queryTags(input: $input) {
                count
                tags {
                    id
                    name
                    description
                    aliases
                    deleted
                    category {
                        id
                        name
                        group
                        description
                    }
                }
            }
        }
        """

        per_page: int = 100
        all_tags = []
        page = 1
        total_count = None

        while True:
            variables = {
                'input': {
                    'page': page,
                    'per_page': per_page,
                    'sort': 'NAME',
                    'direction': 'ASC'
                }
            }

            try:
                data = self._execute_query(query, variables)
                result = data.get('queryTags', {})

                tags = result.get('tags', [])
                if total_count is None:
                    total_count = result.get('count', 0)
                    logging.info(f"Fetching {total_count} tags from StashDB...")

                # Filter out deleted tags and convert to Tag objects
                active_tags = [
                    self._tag_from_graphql(tag)
                    for tag in tags
                    if not tag.get('deleted', False)
                ]
                all_tags.extend(active_tags)

                logging.info(f"Fetched page {page}: {len(tags)} tags ({len(all_tags)}/{total_count} total)")

                # Check if we've fetched all tags
                if len(tags) < per_page or len(all_tags) >= total_count:
                    break

                page += 1

            except Exception as e:
                logging.error(f"Failed to fetch page {page}: {e}")
                raise

        logging.info(f"Successfully fetched {len(all_tags)} active tags")
        return all_tags

    def _tag_from_graphql(self, tag_data: Dict) -> Tag:
        """
        Convert GraphQL tag response to Tag object.

        Args:
            tag_data: Tag dictionary from GraphQL response

        Returns:
            Tag object
        """
        category_name = None
        if tag_data.get('category'):
            category_name = tag_data['category'].get('name')

        # Extract stash ID from tag ID
        stash_id = tag_data['id']

        return Tag(
            name=tag_data['name'],
            description=tag_data.get('description') or '',
            stash_id=stash_id,
            aliases=tag_data.get('aliases', []),
            category=category_name,
            url=f"https://stashdb.org/tags/{stash_id}"
        )

    def find_tag(self, name: Optional[str] = None, tag_id: Optional[str] = None) -> Optional[Tag]:
        """
        Find a single tag by name or ID.

        Args:
            name: Tag name
            tag_id: Tag ID

        Returns:
            Tag object or None if not found
        """
        query = """
        query FindTag($name: String, $id: ID) {
            findTag(name: $name, id: $id) {
                id
                name
                description
                aliases
                deleted
                category {
                    id
                    name
                    group
                    description
                }
            }
        }
        """

        variables = {}
        if name:
            variables['name'] = name
        if tag_id:
            variables['id'] = tag_id

        if not variables:
            raise ValueError("Either name or tag_id must be provided")

        try:
            data = self._execute_query(query, variables)
            tag = data.get('findTag')

            if tag and not tag.get('deleted', False):
                return self._tag_from_graphql(tag)

            return None

        except Exception as e:
            logging.error(f"Failed to find tag: {e}")
            return None
