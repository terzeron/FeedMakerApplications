#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main():
    state = 0

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
    url_prefix = args[0]

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<li\s+class="chapter\s*"\s+data-level="[^"]+"\s+data-path="[^"]+">', line)
            if m:
                state = 1
            m = re.search(r'<li class="toctree-[^"]+"><a[^>]*href="(?P<link>[^"\#]+)">(?P<title>.+)</a>', line)
            if m:
                link = url_prefix + m.group("link")
                title = m.group("title")
                result_list.append((link, title))
                state = 0
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)">', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r' ', '%20', link)
                state = 2
        elif state == 2:
            m = re.search(r'^\s+(?P<title>\S+.*\S+)\s+$', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 0

    num = 1
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num + 1


if __name__ == "__main__":
    sys.exit(main())
