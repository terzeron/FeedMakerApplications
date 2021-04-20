#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO, URL


def main():
    state = 0
    url_prefix = "https://mingrammer.com/gobyexample/"
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<div id="intro">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)"[^>]*>(?P<title>[^<]+)</a>', line)
            if m:
                link = m.group("link")
                title = m.group("title")
                link = URL.concatenate_url(url_prefix, link)
                result_list.append((link, title))
            m = re.search(r'<p class="footer">', line)
            if m:
                break

    num = 1
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num + 1


if __name__ == "__main__":
    sys.exit(main())
