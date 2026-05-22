#!/usr/bin/env python


import sys
import getopt
from typing import List, Tuple
from urllib.parse import urlsplit, urlunsplit

from utils.translation import Translation

import feedparser


def _strip_query(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def main() -> int:
    num_of_recent_feeds = 1000
    do_translate = False
    do_strip_query = False

    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:ts")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            do_translate = True
        elif o == "-s":
            do_strip_query = True

    result_list: List[Tuple[str, str]] = []
    seen: set[str] = set()
    content = sys.stdin.read()
    feed = feedparser.parse(content)

    for entry in feed.entries:
        title = " ".join((entry.get("title", "") or "").split())
        link = (entry.get("link", "") or "").strip()
        if do_strip_query:
            link = _strip_query(link)
        if not link or not title or link in seen:
            continue
        seen.add(link)
        result_list.append((link, title))

    if do_translate:
        translation = Translation()
        result_list = translation.translate(result_list[:num_of_recent_feeds])

    for link, title in result_list[:num_of_recent_feeds]:
        title = " ".join(title.split())
        print(f"{link}\t{title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
