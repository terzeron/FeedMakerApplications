#!/usr/bin/env python


import sys
import re
import getopt
import json
from bs4 import BeautifulSoup, Comment
from pathlib import Path
from bin.feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    feed_dir_path = Path.cwd()

    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == "-f":
            feed_dir_path = Path(a)
    
    state = 0
    url_prefix = "https://hackernoon.com"
    result_list = []
    
    html = IO.read_stdin()
    soup = BeautifulSoup(html, "lxml")
    codes = [tag.string or "" for tag in soup.find_all("script", src=False)]
    for code in codes:
        if code.startswith("{") and code.endswith("}"):
            data = json.loads(code)
            if "props" in data:
                props = data["props"]
                if "pageProps" in props:
                    page_props = props["pageProps"]
                    if "topTags" in page_props:
                        top_tags = page_props["topTags"]
                        for tag in top_tags:
                            if "stories" in tag:
                                stories = tag["stories"]
                                for story in stories:
                                    if "title" in story and "slug" in story:
                                        link = f"{url_prefix}/{story['slug']}"
                                        result_list.append((link, story["title"]))


    for link, title in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

        
if __name__ == "__main__":
    sys.exit(main())
