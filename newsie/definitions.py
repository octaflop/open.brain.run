import os
import ssl

from dagster import (
    Definitions,
    FilesystemIOManager,
    define_asset_job,
    load_assets_from_modules,
    EnvVar,
    job, op
)
from dagster_duckdb_pandas import DuckDBPandasIOManager
from dagster_slack import SlackResource
import duckdb
from . import assets
from .constants import PROJECT_DIR

if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

duckdb_connection = duckdb.connect()
duckdb_connection.execute("SET GLOBAL pandas_analyze_sample=100000")

webscraper_assets = load_assets_from_modules([assets])
everything_job = define_asset_job("DoItAll", selection="*")

news_scrapes = define_asset_job(
    "NewScrapes", selection=webscraper_assets
)


@op
def slack_hi(slack: SlackResource):
    slack.get_client().chat_postMessage(channel="#general", text=":wave: Howdy!")


@job
def summarized_job():
    slack_hi()


DUCKDB_DB_NAME = "newscraper"
DB_PATH = os.path.join(PROJECT_DIR, f"{DUCKDB_DB_NAME}.duckdb")

resources = {
    "io_manager": FilesystemIOManager(),
    "db_io_manager": DuckDBPandasIOManager(
        database=DB_PATH
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
        news_scrapes,
        everything_job,
        summarized_job
    ],
    resources=resources,
)
