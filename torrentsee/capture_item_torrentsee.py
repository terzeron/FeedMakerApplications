#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO


def main() -> int:
    url_prefix: str = ""
    link: str = ""
    title: str = ""
    state: int = 0

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https://torrentsee[^"]+\.com)/[^"]*"/>', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div class="\s*sub_title\s*">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'^\s*<a href="(?P<link>/topic/\d+)">\s*$', line)
            if m:
                link = url_prefix + m.group("link")
                state = 3
        elif state == 3:
            m = re.search(r'^\s*(?P<title>.+?)\s*(</?\w+[^>]*>)?$', line)
            if m:
                title = m.group("title")
                title = re.sub(r'\s*</?\w+[^>]*>', '', title)
                title = re.sub(r'\s*\[email&#160;protected\]', '', title)
                result_list.append((link, title))
                state = 2

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
