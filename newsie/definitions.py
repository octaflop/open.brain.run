import os
import ssl

from dagster import (
    Definitions,
    FilesystemIOManager,
    define_asset_job,
    AssetSelection,
    load_assets_from_modules,
    EnvVar,
    job, op
)
from dagster_duckdb_pandas import DuckDBPandasIOManager
from dagster_slack import SlackResource
from . import assets
from .constants import PROJECT_DIR

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

webscraper_assets = load_assets_from_modules([assets])
everything_job = define_asset_job("everything_everywhere_job", selection="*")
scrape_scholar_job = define_asset_job(
    "NewScrapes", selection=AssetSelection.groups("webscrapers")
)


@op
def slack_hi(slack: SlackResource):
    slack.get_client().chat_postMessage(channel="#general", text=":wave: Howdy!")


@job
def summarized_job():
    slack_hi()


resources = {
    "io_manager": FilesystemIOManager(),
    "db_io_manager": DuckDBPandasIOManager(
        database=os.path.join(PROJECT_DIR, "example.duckdb")
    ),
    "slack": SlackResource(token=EnvVar("BOT_SLACK_TOKEN"))
}

# all_sensors = [
#     check_new_articles_sensor,
# ]
all_assets = [*webscraper_assets]

defs = Definitions(
    assets=all_assets,
    jobs=[
        scrape_scholar_job,
        everything_job,
        summarized_job
    ],
    resources=resources,
)
