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
    
    numOfRecentFeeds = 20
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = feedmakerutil.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        if state == 0:
            m = re.search(r'<li class="list viewerLinkBtn (?:pointer )?list_[HV][^>]*data-productid="(?P<id>\d+)', line)
            if m:
                productid = m.group("id")
                link = "http://page.kakao.com/viewer?productId=" + productid
                state = 1
        elif state == 1:
            m = re.search(r'<span class="Lfloat (?:listTitle )?ellipsis">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'^\s*(?P<title>\S+.*\S+)\s*$', line)
            if m:
                title = m.group("title")
                title = re.sub(r'&(lt|gt);', '', title)
                resultList.append((link, title))
                state = 0

    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))
        

if __name__ == "__main__":
    main()
