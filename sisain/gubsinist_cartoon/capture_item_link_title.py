#!/usr/bin/env python


import re
import sys
import getopt
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://sisain.co.kr"
    state = 0

    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<a href="(?P<link>/news/articleView.html\?idxno=\d+)" target="_top">', line)
            if m:
                link = url_prefix + m.group("link")
                state = 1
        elif state == 1:
            m = re.search(r'\s*(?P<title>.+?)\s*</a>', line)
            if m:
                title = m.group("title")
                if "굽시니스트" in title:
                    result_list.append((link, title))
                state = 2
        elif state == 2:
            m = re.search(r'</li>', line)
            if m:
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")


if __name__ == "__main__":
    sys.exit(main())
