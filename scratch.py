import urllib

from typing import List

import ssl
import feedparser
import pandas as pd
from bs4 import BeautifulSoup

from newsie.constants import FEED_URL


if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context =  ssl._create_unverified_context


def extract_links(html_content_list: List):
    html_content = html_content_list[0]['value'] if html_content_list else ''

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

def run():
    feed = feedparser.parse(FEED_URL)
    df = pd.DataFrame(feed.entries)

    content = [e.get('content')[0].get('value') for e in feed.entries]
    df['link_texts'], df['link_hrefs'] = zip(*df['content'].apply(extract_links))
    content_list_len = [len(e.get('content')) for e in feed.entries]
    crawled_df = df[['id', 'link_texts', 'link_hrefs']].copy()
    crawled_df = crawled_df.set_index(['id']).apply(lambda x: x.explode()).reset_index()
    merged_df = pd.merge(crawled_df, df, on='id', how='left')

    crawled_df['raw_html'] = crawled_df['link_hrefs'].astype(str).replace('nan', '').apply(extract_html)

    additional_links_df = crawled_df.copy()
    additional_links_df['link_texts'], additional_links_df['link_hrefs'] = zip(
        *additional_links_df['raw_html'].apply(extract_links))
    additional_links_df = additional_links_df[['id', 'link_texts', 'link_hrefs']].set_index(['id']).apply(
        lambda x: x.explode()).reset_index()

    # Concatenate the crawled_df with the new dataframe additional_links_df
    final_df = pd.concat([crawled_df, additional_links_df], ignore_index=True)

    return df, content, crawled_df, merged_df, final_df


if __name__ == "__main__":
    run_log = run()
    print(run_log)
