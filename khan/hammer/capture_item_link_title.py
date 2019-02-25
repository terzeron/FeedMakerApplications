#!/usr/bin/env python3


import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    link_prefix = "http://news.khan.co.kr/kh_cartoon/"
    
    numOfRecentFeeds = 10
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
    
    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        m1 = re.search(r'<a href="\./(?P<link>khan_index\.html\?artid=\d+)[^"]*">(?P<title>[^<]+)</a>', line)
        if m1:
            link = link_prefix + m1.group("link")
            title = m1.group("title")
            resultList.append((link, title))

    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))

if __name__ == "__main__":
    sys.exit(main())
