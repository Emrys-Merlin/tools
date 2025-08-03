# Literature Mover

At some point, I built my own literature lister in [notion](https://notion.so). This became too tedious and I decided to migrate to [Zotero](https://zotero.org). To avoid having to transfer all the entries manually, I created this tool.

## My notion setup

My literature list consisted of a big notion database (a table) with a few key columns:
- Title
- First Author
- Publication year
- URL
- Status (to read, already read)
- Tags
- File name

I would store the pdfs in my personal [pcloud](https://pcloud.com) in a certain directory under the file name specified in the table.

## The tool

The tool performs the following steps

1. It downloads the raw database from notion
2. It extracts the columns from the properties dictionary in the raw table
3. It creates Zotero entries and checks if a pdf exists. If yes, it uploads it as an attachement to the entry.

## Installation

This project is pip installable.

## Usage

The package install the command line tool `lit-mover`. To use it, you need API access to both notion and Zotero. This is taken care of using ENV variables:

```bash
export NOTION_DATABASE=the database id
export NOTION_TOKEN=your notion api token - keep this secret

export ZOTERO_USER_ID=your user id
export ZOTERO_TOKEN=your zotero api token - keep this secret
```
You can find out how to get the notion API info [here](https://developers.notion.com/docs/create-a-notion-integration) and the Zotero API info [here](https://pyzotero.readthedocs.io/en/latest/#getting-started-short-version).

Afteward, you can simply run
```bash
lit-mover sync
```
It takes two flags `--literature-dir` which you can point to a directory containting the pdf files you want to upload and `--skip`, which will skip the first `n` entries. The second flag is useful when you run into Zotero rate limits (I was too lazy to add an automatic backoff).

If you would like to manually inspect the data before the sync, you can alos run three individual commands:
- `lit-mover download` will download the notion database and store it in a parquet file.
- `lit-mover format` will transform the raw notion table into something human-readable and importable into Zotero.
- `lit-mover upload` will upload the entries to Zotero.

Each subcommand has a help test (`--help`) explaining its usage.
