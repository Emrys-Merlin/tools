from pathlib import Path

import polars as pl
from typer import Typer, echo

from lit_mover.notion import NotionSettings
from lit_mover.transform import transform_database
from lit_mover.zotero import ZoteroSettings

main = Typer()


@main.command()
def download(
    database_fn: Path,
):
    """Download the literature database from Notion and save it to DATABASE_FN."""
    settings = NotionSettings()

    echo(f"Downloading database to {database_fn}")
    df = settings.get_database()
    df.write_parquet(database_fn)
    echo(f"Database with {len(df)} entries saved to {database_fn}")


@main.command()
def format(
    input_fn: Path,
    output_fn: Path,
):
    """Format the literature database from INPUT_FN and save it to OUTPUT_FN."""
    df = pl.read_parquet(input_fn)
    new_df = transform_database(df)
    echo(new_df.head())
    new_df.write_parquet(output_fn)


@main.command()
def upload(
    database_fn: Path,
    literature_dir: Path | None = None,
    skip: int = 0,
):
    """Upload the literature database to Zotero.

    The database is read from DATABASE_FN and the literature files are expected to be in
    --literature-dir. You can skip the first SKIP entries in the database.
    """
    echo(f"Uploading database from {database_fn}")
    zotero_settings = ZoteroSettings()
    df = pl.read_parquet(database_fn)

    df = df.tail(max(len(df) - skip, 0))

    zotero_settings.upload_db(
        df=df,
        literature_dir=literature_dir,
    )

    echo(f"Uploaded {len(df)} entries to Zotero.")


@main.command()
def sync(
    literature_dir: Path | None = None,
    skip: int = 0,
):
    """Sync the literature database from Notion to Zotero.

    The literature files are expected to be in --literature-dir. You can skip the first SKIP entries
    in the database.
    """
    notion_settings = NotionSettings()
    zotero_settings = ZoteroSettings()

    df = notion_settings.get_database()
    df = transform_database(df)
    df = df.tail(max(len(df) - skip, 0))
    zotero_settings.upload_db(
        df=df,
        literature_dir=literature_dir,
    )


if __name__ == "__main__":
    main()
