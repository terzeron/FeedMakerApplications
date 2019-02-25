#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    state = 0

    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        if state == 0:
            m = re.search(r'<a href="(?P<link>[^"]+)">', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                state = 1
        elif state == 1:
            m = re.search(r'<div class="title"', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'\s*(<span[^>]*>\w+</span>)?\s*(?P<title>\S.+)\s*</div>', line)
            if m:
                title = m.group("title")
                resultList.append((link, title))
                state = 0

    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
