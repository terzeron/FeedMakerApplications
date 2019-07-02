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
    url_prefix = ""
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
            m = re.search(r'g5_url\s+=\s+"(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+bo_table=[^"]+wr_id=\d+)">', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                state = 2
        elif state == 2:
            m = re.search(r'<div class="title"', line)
            if m:
                state = 3
        elif state == 3:
            m = re.search(r'\s*(<span[^>]*>.*</span>)?\s*(?P<title>\S.+)\s*<span[^>]*>', line)
            if m:
                title = m.group("title")
                title = re.sub(r"\s+", " ", title)
                resultList.append((link, title))
                state = 1

    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
