#!/usr/bin/env python3


import os
import sys
import re
import getopt
import feedmakerutil


def main():
    numOfRecentFeeds = 100
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
    
    lineList = feedmakerutil.read_stdin_as_line_list()
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
