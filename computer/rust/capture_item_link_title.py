#!/usr/bin/env python


import sys
import re
from feed_maker_util import IO


def main():
    state = 0
    num_of_recent_feeds = 1000
    result_list = []

    for line in IO.read_stdin_as_line_list():
        m = re.search(r'(?P<link>.*)\t(?P<title>.*)', line)
        if m:
            link = m.group("link")
            title = m.group("title")
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
