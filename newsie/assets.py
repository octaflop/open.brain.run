import json
from typing import List

import urllib

import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

from .constants import FEED_URL
from .ai import generate_summary
from dagster import asset, Config, AssetExecutionContext
from dagster_slack import SlackResource

from .constants import FEED_DT_FMT
from .utils import query_news, extract_html


def get_summary(text, model, context, slack):
    summary = generate_summary(
        text,
        model=model,
    )
    context.log.info(f"Generated summary:\n{summary}")
    slack.get_client().chat_postMessage(channel="#general", text=f"{summary.get('output_text', 'No summary sads')}")
    return summary


def extract_links(html_content_list: List):
    try:
        html_content = html_content_list[0]['value'] if html_content_list else ''
    except Exception as e:
        print(e)
        return [], []

    soup = BeautifulSoup(html_content, "html.parser")
    links = [(a.text, a['href']) for a in soup.find_all('a', href=True)]
    link_texts = [link[0] for link in links]
    link_hrefs = [link[1] for link in links]
    return link_texts, link_hrefs


def extract_html(html_link):
    if html_link == '':
        return
    try:
        print(f"Now reading {html_link}")
        html_resp = urllib.request.urlopen(html_link).read()
    except urllib.error.HTTPError as e:
        print(e)
        return None
    except urllib.error.URLError as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None
    soup = BeautifulSoup(html_resp, "html.parser")
    article = str(soup.find("article"))
    print(f"Got an article with len {len(article)}")
    return article


class SummarizationConfig(Config):
    # https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo
    model: str = "gpt-3.5-turbo-1106"
    chunk_size: int = 4000
    max_tokens: int = 3000


@asset(io_manager_key="db_io_manager")
def gathered_news(context) -> pd.DataFrame:
    feed = feedparser.parse(FEED_URL)
    df = pd.DataFrame(feed.entries)

    df['link_texts'], df['link_hrefs'] = zip(*df['content'].apply(extract_links))
    return df


@asset(io_manager_key="db_io_manager")
def crawl_news(context, gathered_news):
    crawled_df = gathered_news[['id', 'link_texts', 'link_hrefs']].copy()
    crawled_df = crawled_df.set_index(['id']).apply(lambda x: x.explode()).reset_index()

    crawled_df['raw_html'] = crawled_df['link_hrefs'].astype(str).replace('nan', '').apply(extract_html)

    additional_links_df = crawled_df.copy()
    additional_links_df['link_texts'], additional_links_df['link_hrefs'] = zip(
        *additional_links_df['raw_html'].apply(extract_links))
    additional_links_df = additional_links_df[['id', 'link_texts', 'link_hrefs']].set_index(['id']).apply(
        lambda x: x.explode()).reset_index()
    return additional_links_df


@asset(io_manager_key="db_io_manager")
def download_html(
        context: AssetExecutionContext, gathered_news: pd.DataFrame, crawl_news: pd.DataFrame
) -> pd.DataFrame:
    # Drop news which didn't get text
    gather_news = gathered_news.dropna(subset=["link_texts"])
    # Concatenate the crawled_df with the new dataframe additional_links_df
    final_df = pd.concat([crawl_news, gather_news], ignore_index=True)

    return final_df


@asset(io_manager_key="db_io_manager")
def summarize_articles(
        context, download_html: pd.DataFrame, config: SummarizationConfig, slack: SlackResource
) -> pd.DataFrame:
    download_html.dropna(subset=['content'], inplace=True)
    download_html['content'] = download_html['content'].astype(str)
    download_html = download_html[download_html['content'].str.len() >= 100]
    download_html["summary"] = download_html["content"].apply(
        lambda x: get_summary(x, config.model, context, slack)
    )

    return download_html
