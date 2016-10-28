#!/usr/bin/env python

import os
import sys
import re
import getopt
import feedmakerutil


def main():
    link = ""
    title = ""
    state = 0
    
    numOfRecentFeeds = 10
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = feedmakerutil.readStdinAsLineList()
    resultList = []
    for line in lineList:
        if state == 0:
            m1 = re.search(r'<li class="list viewerLinkBtn (?:pointer )?list_[HV][^>]*data-productid="(?P<id>\d+)', line)
            if m1:
                productid = m1.group("id")
                link = "http://page.kakao.com/viewer?productId=" + productid
                state = 1
        elif state == 1:
            m2 = re.search(r'<span class="Lfloat (?:listTitle )?ellipsis">', line)
            if m2:
                state = 2
        elif state == 2:
            m3 = re.search(r'^\s*(?P<title>\S+.*\S+)\s*$', line)
            if m3:
                title = m3.group("title")
                title = re.sub(r'&(lt|gt);', '', title)
                resultList.append((link, title))
                state = 0

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
        

if __name__ == "__main__":
    main()
