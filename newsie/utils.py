import time
import urllib.request
from typing import List, Sequence

import feedparser
from bs4 import BeautifulSoup
from dagster import AssetExecutionContext
from dagster_slack import SlackResource
from langchain_core.documents import Document

from newsie.ai import generate_summary, generate_metadata


def query_news(url: str, num_tries: int = 10):
    for i in range(num_tries):
        try:
            response = urllib.request.urlopen(url).read()
            feed = feedparser.parse(response)
            feed_len = len(feed.entries)
            if feed_len != 0:
                return feed
            else:
                raise ValueError("feed_len is 0")
        except ValueError:
            if i < num_tries - 1:  # Don't sleep on last iteration
                time.sleep(2**i)  # Exponential back off

            else:
                raise Exception(f"Query failed after {num_tries} tries")


def extract_html(link, context: AssetExecutionContext):
    html_link = link.get("html_link")
    context.log.info(f"Now retrieving {html_link}")
    try:
        html_resp = urllib.request.urlopen(html_link).read()
    except urllib.error.HTTPError as e:
        context.log.warning(f"HTTPError when retrieving {html_link}: {e}")
        return None
    except Exception as e:
        context.log.error(f"Exception when retrieving {html_link}: {e}")
        return None
    soup = BeautifulSoup(html_resp, "html.parser")
    article = str(soup.find("article"))
    context.log.info(
        f"Captured {len(article)} chars from article html of {link.get('title')}"
    )
    return article


def get_summary(text: str, model: str, context: AssetExecutionContext, slack: SlackResource):
    summary = generate_summary(
        text,
        model=model,
    )
    context.log.info(f"Generated summary:\n{summary}")
    slack.get_client().chat_postMessage(channel="#general", text=f"{summary.get('output_text', 'No summary sads')}")
    return summary


def extract_metadata(text: str, model: str, context: AssetExecutionContext, slack: SlackResource) -> Sequence[Document]:
    metadata = generate_metadata(
        text,
        model=model
    )
    context.log.info(f"Generated metadata for article:\n {metadata}")
    slack_msg = f"""
    Pulled Metadata for article:
    {metadata}
    """
    slack.get_client().chat_postMessage(channel="#general", text=slack_msg)
    return metadata


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


# def extract_html(html_link):
#     if html_link == '':
#         return
#     try:
#         print(f"Now reading {html_link}")
#         html_resp = urllib.request.urlopen(html_link).read()
#     except urllib.error.HTTPError as e:
#         print(e)
#         return None
#     except urllib.error.URLError as e:
#         print(e)
#         return None
#     except Exception as e:
#         print(e)
#         return None
#     soup = BeautifulSoup(html_resp, "html.parser")
#     article = str(soup.find("article"))
#     print(f"Got an article with len {len(article)}")
#     return article
