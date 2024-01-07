import time
import urllib.request

import feedparser
from bs4 import BeautifulSoup


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


def extract_html(link, context):
    html_link = link.get("html_link")
    context.log.info(f"Now retrieving {html_link}")
    try:
        html_resp = urllib.request.urlopen(html_link).read()
    except urllib.error.HTTPError as e:
        context.log.warning(f"HTTPError when retrieving {html_link}: {e}")
        return None
    soup = BeautifulSoup(html_resp, "html.parser")
    article = str(soup.find("article"))
    context.log.info(
        f"Captured {len(article)} chars from article html of {link.get('title')}"
    )
    return article
