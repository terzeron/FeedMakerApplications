#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main():
    url_prefix = "https://kotlinlang.org/docs/"

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str]] = []
    for line in line_list:
        matches = re.findall(r'<li[^>]*><a\s+[^>]*href="(?P<link>[^"]+)"[^>]*>(?P<title>[^>]+)</a></li>', line)
        for match in matches:
            if match[0].startswith("http"):
                link = match[0]
            else:
                link = url_prefix + match[0]
            title = match[1]
            result_list.append((link, title))

    num = 1
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d %s" % (link, num, title))
        num = num + 1


if __name__ == "__main__":
    sys.exit(main())
