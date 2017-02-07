#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
import collections
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = ""
    state = 0
    
    numOfRecentFeeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    resultList = []
    for line in feedmakerutil.readStdinAsLineList():
        if state == 0:
            m = re.search(r'href="(?P<url_prefix>http://[^"/]+)"', line)
            if m:
                urlPrefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<article_id>/\d+)" class="link_post">', line)
            if m:
                link = urlPrefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(r'<strong class="tit_post">(?P<title>.+)</strong>', line)
            if m:
                title = m.group("title")
                resultList.append((link, title))
                state = 1

    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    main()
        
