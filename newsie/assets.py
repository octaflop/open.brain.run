

import feedparser
import pandas as pd

from .constants import FEED_URL
from dagster import asset, Config, AssetExecutionContext
from dagster_slack import SlackResource

from .utils import extract_html, get_summary, extract_links


class SummarizationConfig(Config):
    # https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo
    model: str = "gpt-3.5-turbo-1106"
    chunk_size: int = 4000
    max_tokens: int = 3000



@asset(io_manager_key="db_io_manager")
def gathered_news(context: AssetExecutionContext) -> pd.DataFrame:
    context.log.info(f"Parsing {FEED_URL}")
    feed = feedparser.parse(FEED_URL)
    df = pd.DataFrame(feed.entries)
    context.log.info(f"Parsed {FEED_URL} to df, now extracting links")

    df['link_texts'], df['link_hrefs'] = zip(*df['content'].apply(extract_links))
    context.log.info(f"Parsed {FEED_URL} to f{df.head()}")
    return df


@asset(io_manager_key="db_io_manager")
def crawl_news(context: AssetExecutionContext, gathered_news):
    crawled_df = gathered_news[['id', 'link_texts', 'link_hrefs']].copy()
    crawled_df = crawled_df.set_index(['id']).apply(lambda x: x.explode()).reset_index()

    crawled_df['raw_html'] = crawled_df['link_hrefs'].astype(str).replace('nan', '').apply(extract_html)

    additional_links_df = crawled_df.copy()
    additional_links_df['link_texts'], additional_links_df['link_hrefs'] = zip(
        *additional_links_df['raw_html'].apply(extract_links))
    additional_links_df = additional_links_df[['id', 'link_texts', 'link_hrefs']].set_index(['id']).apply(
        lambda x: x.explode()).reset_index()

    context.log.info(additional_links_df.head())
    return additional_links_df


@asset(io_manager_key="db_io_manager")
def download_html(
        context: AssetExecutionContext, gathered_news: pd.DataFrame, crawl_news: pd.DataFrame
) -> pd.DataFrame:
    # Drop news which didn't get text
    gather_news = gathered_news.dropna(subset=["link_texts"])
    # Concatenate the crawled_df with the new dataframe additional_links_df
    final_df = pd.concat([crawl_news, gather_news], ignore_index=True)
    context.log.info(final_df.head())

    return final_df

@asset(io_manager_key="db_io_manager")
def grok_metadata(
        context: AssetExecutionContext, download_html: pd.DataFrame, config: SummarizationConfig, slack: SlackResource
) -> pd.DataFrame:
    download_html.dropna(subset=['content'], inplace=True)
    download_html['content'] = download_html['content'].astype(str)
    download_html = download_html[download_html['content'].str.len() >= 100]
    download_html["doc_metadata"] = download_html["content"].apply(
        lambda x: grok_metadata(x, config.model, context, slack)
    )

    return download_html

@asset(io_manager_key="db_io_manager")
def summarize_articles(
        context: AssetExecutionContext, download_html: pd.DataFrame, config: SummarizationConfig, slack: SlackResource
) -> pd.DataFrame:
    download_html.dropna(subset=['content'], inplace=True)
    download_html['content'] = download_html['content'].astype(str)
    download_html = download_html[download_html['content'].str.len() >= 100]
    download_html["summary"] = download_html["content"].apply(
        lambda x: get_summary(x, config.model, context, slack)
    )

    return download_html
