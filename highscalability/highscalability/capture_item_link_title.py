#!/usr/bin/env python3


import os
import sys
import re
import getopt
import feedmakerutil


def main():
    linkPrefix = "http://highscalability.com"
    
    numOfRecentFeeds = 10
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
    
    lineList = feedmakerutil.readStdinAsLineList()
    resultList = []
    for line in lineList:
        matches = re.findall(r'<li><a href="(/blog/[^"]+.html)">([^<]+)</a></li>', line)
        for match in matches:
            link = match[0]
            link = linkPrefix + link
            title = match[1]
            if title.startswith("Stuff The Internet Says On Scalability") or title.startswith("Sponsored Post:"):
                continue
            resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))

if __name__ == "__main__":
    main()
