#!/usr/bin/env python3


import os
import sys
import re
import getopt
from feedmakerutil import IO

def main():
    url_prefix = "http://mmzone.co.kr/mms_tool/"
    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        m = re.search(r'<div id="md_text_title" onclick="location.href=\'(?P<link>[^"]+no=\d+)&[^"]+\'"[^>]*>(?P<title>.+)</div>', line)
        if m:
            if m.group("link").startswith("javascript"):
                continue
            link = url_prefix + m.group("link")
            link = re.sub(r'&amp;', '&', link)
            title = m.group("title")
            resultList.append((link, title))

        m = re.search(r'<a href="(?P<link>[^"]+no=\d+)&[^"]+">(?P<title>.+)</a>', line)
        if m:
            if m.group("link").startswith("javascript"):
                continue
            link = url_prefix + m.group("link")
            link = re.sub(r'&amp;', '&', link)
            title = m.group("title")
            resultList.append((link, title))
                              
    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
