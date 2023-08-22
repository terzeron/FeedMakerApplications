#!/usr/bin/env python


import os
import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    state = 0
    linkPrefix = "http://www.popit.kr"
    
    numOfRecentFeeds = 100
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
    
    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        if state == 0:
            m1 = re.search(r'<p class="feed-publish-message">(?P<title>.*)</p>', line)
            if m1:
                title = m1.group("title")
                state = 1
        elif state == 1:
            m2 = re.search(r'<a [^>]*href="(?P<link>[^"]+)">', line)
            if m2:
                link = linkPrefix + m2.group("link")
                resultList.append((link, title))
                state = 0

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))

if __name__ == "__main__":
    main()
