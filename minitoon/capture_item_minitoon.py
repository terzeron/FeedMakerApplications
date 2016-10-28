#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
import feedmakerutil


def main():
    link_prefix = "http://minitoon.net"
    link = ""
    title = ""

    numOfRecentFeeds = 20
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = feedmakerutil.readStdinAsLineList()
    resultList = []
    for line in lineList:
        m = re.search(r'<a class="gal_subject" href="(?P<link>.+)" target="_blank">(?P<title>.+)</a>', line)
        if m:
            link = m.group("link")
            link = link_prefix + re.sub(r'&amp;', '&', link)
            title = m.group("title")
            title = re.sub(r'&amp;', '&', title)
            resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
            
if __name__ == "__main__":
    main()
        
