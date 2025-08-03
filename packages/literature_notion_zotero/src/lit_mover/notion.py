import polars as pl
from notion_client import Client
from notion_client.helpers import collect_paginated_api
from pydantic_settings import BaseSettings, SettingsConfigDict


class NotionSettings(BaseSettings):
    token: str
    database: str

    _client: Client | None = None

    model_config = SettingsConfigDict(
        env_prefix="NOTION_",
    )

    @property
    def client(self) -> Client:
        """Returns a Notion client instance using the configured token."""
        if self._client is None:
            self._client = Client(auth=self.token)
        return self._client

    def get_database(self) -> pl.DataFrame:
        """Retrieves the database information for the configured database ID."""
        return pl.DataFrame(
            collect_paginated_api(
                self.client.databases.query,
                database_id=self.database,
            ),
            infer_schema_length=None,
        )
