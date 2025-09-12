#!/usr/bin/env python


import sys
import getopt
from typing import List, Tuple

from utils.translation import Translation

import feedparser


def main() -> int:
    num_of_recent_feeds = 1000
    do_translate = False
    
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:t")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            do_translate = True
            
    result_list: List[Tuple[str, str]] = []
    content = sys.stdin.read()
    feed = feedparser.parse(content)

    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        result_list.append((link, title))

    if do_translate:
        translation = Translation()
        result_list = translation.translate(result_list[:num_of_recent_feeds])
    
    for (link, title) in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

    return 0
        

if __name__ == "__main__":
    sys.exit(main())
