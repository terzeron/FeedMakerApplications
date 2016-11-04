#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
import feedmakerutil


def main():
    link_prefix = "http://www.myktoon.com/web/times_view.kt?"
    link = ""
    title = ""
    
    numOfRecentFeeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
        
    lineList = feedmakerutil.readStdinAsLineList()
    state = 0
    resultList = []
    for line in lineList:
        if state == 0:
            m1 = re.search(r'<a href="/web/times_view.kt[^"]*webtoonseq=(?P<webtoonseq>\d+)&(amp;)?timesseq=(?P<timesseq>\d+)">', line)
            if m1:
                webtoonseq = m1.group("webtoonseq")
                timesseq = m1.group("timesseq")
                link = link_prefix + "webtoonseq=" + webtoonseq + "&timesseq=" + timesseq
                state = 1
        elif state == 1:
            m2 = re.search(r'<span class="bkTitle">(?P<title>[^<]+)</span>', line)
            if m2:
                title = m2.group("title")
                resultList.append((link, title))
                state = 0

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
            
if __name__ == "__main__":
	main()

