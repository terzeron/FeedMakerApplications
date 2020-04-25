#!/usr/bin/env python


#import io
#import os
import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO


def main() -> int:
    link: str = ""
    title: str = ""
    num: int = 0
    state: int = 0

    num_of_recent_feeds: int = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list: List[str] = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<h2 class="entry-title">', line)
            if m:
                state = 1
            if re.search(r'<div class="latest-news-wrapper">', line):
                break
        elif state == 1:
            m = re.search(r'<a [^>]*href="(?P<link>https?://[^"]+)">(?P<title>.+)</a>', line)
            if m:
                link = m.group("link")
                title = m.group("title")
                link = re.sub(r'&amp;', '&', link)
                link = re.sub(r' ', '+', link)
                title = re.sub(r"\s+", " ", title)
                result_list.append((link, title))
                state = 0

    num = len(result_list)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%d. %s" % (link, num, title))
        num = num - 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
