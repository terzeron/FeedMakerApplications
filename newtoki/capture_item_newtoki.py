#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO


def main() -> int:
    link: str = ""
    title: str = ""
    state = 0

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<a href="(?P<link>[^"]+\/\d+)(\/|\?)[^"]*" class="item-subject">', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                state = 1
        elif state == 1:
            m = re.search(r'^\s*(?P<title>\S+.*\S)\s*(?:<span class="count[^"]*">\d+</span>|</a>)$', line)
            if m:
                title = m.group("title")
                title = re.sub(r'\s+', ' ', title)
                title = re.sub(r'\b(\d\d)(권|화|부|편)', '0\g<1>\g<2>', title)
                title = re.sub(r'\b(\d)(권|화|부|편)', '00\g<1>\g<2>', title)
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
