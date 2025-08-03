from pathlib import Path
from time import sleep
from typing import Self

import polars as pl
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from pyzotero import zotero
from tqdm import tqdm


class ZoteroSettings(BaseSettings):
    """
    Settings for Zotero integration.
    """

    model_config = SettingsConfigDict(env_prefix="ZOTERO_")

    user_id: str
    token: str
    collection: str = "notion upload"
    sleep_sec: int = 5

    _client: zotero.Zotero | None = None

    @property
    def client(self: Self) -> zotero.Zotero:
        """
        Returns a Zotero client instance.
        """
        if self._client is None:
            self._client = zotero.Zotero(self.user_id, "user", self.token)
        return self._client

    def upload_db(
        self: Self,
        *,
        df: pl.DataFrame,
        literature_dir: Path | None = None,
    ) -> None:
        """Uploads the literature database to Zotero.

        Args:
            df: DataFrame containing the literature entries.
            literature_dir: Directory containing the literature files.
        """
        collection_id = self._maybe_create_collection()
        for entry in tqdm(df.to_dicts(), total=len(df), desc="Uploading entries"):
            logger.debug(f"Processing entry: {entry}")
            entry_id = self._upload_entry(
                entry=entry,
                collection_id=collection_id,
            )
            self._maybe_upload_file(
                entry=entry,
                entry_id=entry_id,
                literature_dir=literature_dir,
            )

            sleep(self.sleep_sec)

    def _maybe_create_collection(self: Self) -> str:
        """Creates the collection if it does not exist."""
        for collection in self.client.collections():
            if collection["data"]["name"] == self.collection:
                logger.debug(f"Collection '{self.collection}' already exists")
                return collection["data"]["key"]
        logger.debug(f"Collection '{self.collection}' does not exist, creating it")
        collection = self.client.create_collection([{"name": self.collection}])
        return collection["data"]["key"]

    def _upload_entry(self: Self, *, entry: dict, collection_id: str) -> str:
        """Creates a Zotero item from a literature entry."""
        item = self.client.item_template("journalArticle")
        item["title"] = entry["title"]
        item["creators"] = [
            {
                "creatorType": "author",
                "firstName": "",
                "lastName": entry["first_author"],
            }
        ]
        item["date"] = str(entry["year"])
        item["url"] = entry["url"]
        item["tags"] = [{"tag": entry["status"]}] + [{"tag": tag} for tag in entry["tags"]]
        item["collections"] = [collection_id]
        self.client.check_items([item])
        resp = self.client.create_items([item])
        if len(resp["success"]) == 0:
            logger.error(f"Failed to create item: {resp['failed']}")
            raise RuntimeError(f"Failed to create item: {resp['failed']}")

        return resp["success"]["0"]

    def _maybe_upload_file(
        self: Self,
        *,
        entry_id: str,
        entry: dict,
        literature_dir: Path | None = None,
    ) -> None:
        """Uploads the file associated with the literature entry to Zotero."""
        if "file_name" not in entry or not entry["file_name"] or not literature_dir:
            logger.debug("No file to upload")
            return

        file_path = literature_dir / entry["file_name"]
        if not file_path.exists():
            logger.warning(f"File {file_path} does not exist, skipping upload")
            return

        resp = self.client.attachment_simple(
            files=[str(file_path)],
            parentid=entry_id,
        )
        if len(resp["failure"]) != 0:
            logger.error(f"Failed to upload file: {file_path.name}")
            raise RuntimeError(f"Failed to upload file: {file_path.name}")
