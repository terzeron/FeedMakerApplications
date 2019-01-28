#!/usr/bin/env python3


import os
import sys
import re
import getopt
from feedmakerutil import IO


def main():
    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        m = re.search(r'<a[^>]*href="(?P<link>[^\?"]+)[^"]*">(?P<title>.+)</a>', line)
        if m:
            link = m.group("link")
            link = re.sub(r'&amp;', '&', link)
            title = m.group("title")
            resultList.append((link, title))
                              
    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    main()
