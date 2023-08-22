#!/usr/bin/env python


import os
import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    numOfRecentFeeds = 100
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
    
    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        m1 = re.search(r'<li><a href="(?P<link>[^"]+)">(?P<title>.+)</a>.*</li>', line)
        if m1:
            link = m1.group("link")
            title = m1.group("title")
            resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))

if __name__ == "__main__":
    main()
