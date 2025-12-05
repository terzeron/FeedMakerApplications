#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main() -> int:
    link: str = ""
    title: str = ""
    url_prefix = ""
    state = 0

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https://[^/]+/)[^"]*" ?/>', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div class="chapter-list[^"]*">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'<a href="(?P<link>/chapter/\d+)"', line)
            if m:
                link = m.group("link")
                link = url_prefix + link
                state = 3
        elif state == 3:
            m = re.search(r'<strong class="[^"]*"><i class="[^"]*"></i>\s*(?P<title>.+)\s*<label', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 2

    num = len(result_list)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num - 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
