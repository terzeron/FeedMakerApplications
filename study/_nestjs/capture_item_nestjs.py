#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main():
    state: int = 0
    url_prefix: str = ""
    num_of_recent_feeds: int = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list: List[str] = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^/]+)[^"]*"\s*/?>', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            matches = re.findall(r'<a[^>]*routerlinkactive="active"[^>]*href="(?P<link>[^"]*)"[^>]*>(?P<title>.+?)</a>', line)
            for match in matches:
                link = url_prefix + match[0]
                title = re.sub(r'\s*<!---->\s*', '', match[1])
                title = re.sub(r'(<h3[^>]*>|</h3>)', '', title)
                result_list.append((link, title))

    num = 1
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num + 1


if __name__ == "__main__":
    sys.exit(main())
