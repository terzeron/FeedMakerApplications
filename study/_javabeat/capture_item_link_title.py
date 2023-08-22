#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        m = re.search(r'a href="(?P<link>[^"]+)"[^>]*title="(?P<title>[^"]+)"', line)
        if m:
            link = m.group("link")
            title = m.group("title")
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
