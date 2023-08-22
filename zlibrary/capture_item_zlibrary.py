#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://kr1lib.org"

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        m = re.search(r'<a href="(?P<link>/book/[^"]+)" style="[^"]*underline[^"]*">(?P<title>[^<]+)</a>', line)
        if m:
            link = url_prefix + m.group("link")
            title = m.group("title")
            if re.search(r'(한국어|grammar|korean|vocabular|어휘|문법|topik)', title, re.IGNORECASE):
                continue
            result_list.append((link, title))

    num = len(result_list)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))
        num = num - 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
