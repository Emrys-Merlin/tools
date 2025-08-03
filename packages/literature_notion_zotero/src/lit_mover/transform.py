import polars as pl


def get_property(
    properties: dict,
    keys: list[str | int],
) -> str | int | float:
    values = properties
    try:
        for key in keys:
            values = values[key]
    except Exception:
        return ""

    if not isinstance(values, str | int | float):
        return ""

    return values


def transform_properties(properties: dict) -> dict:
    res = {
        # TODO
        "title": get_property(properties, ["Title", "title", 0, "plain_text"]),
        "first_author": get_property(properties, ["First Author", "select", "name"]),
        "year": get_property(properties, ["Year", "number"]),
        "file_name": get_property(properties, ["File Name", "formula", "string"]),
        "url": get_property(properties, ["Link", "url"]),
        "tags": [tag["name"] for tag in properties["Tags"]["multi_select"]],
        "status": get_property(properties, ["Status", "select", "name"]),
    }

    return res


def transform_database(df: pl.DataFrame) -> pl.DataFrame:
    return df.select(pl.col("properties").map_elements(transform_properties)).unnest("properties")
