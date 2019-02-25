#!/usr/bin/env python3


import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    state = 0
    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        if state == 0:
            m = re.search(r'<a class="deco" href="(?P<link>[^\?"]+)[^"]*">(?P<title>.+)</a>', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                title = m.group("title")
                state = 1
        elif state == 1:
            m = re.search(r'<a class="nick"[^>]*>\s*ㅣ\s*(?P<author>.*?)\s*</a>', line)
            if m:
                author = m.group("author")
                title = title + " | " + author
                resultList.append((link, title))
                state = 0
                              
    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
