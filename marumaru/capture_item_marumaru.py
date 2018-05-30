#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
from feedmakerutil import IO


def main():
    link = ""
    title = ""

    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        matches = re.findall(r'<a href="(?P<link>http[^"]+)"[^>]*>(?:<(?:span|font)[^>]*>)*(?P<title>(?!</?\w+).*?(?:화|권|부|편)[^<]*)(?:</(?:span|font)>)*</a>', line)
        for m in matches:
            link = m[0]
            link = re.sub(r'&amp;', '&', link)
            link = re.sub(r'http://(www.shencomics|www.yuncomics|blog.yuncomics).com', 'http://wasabisyrup.com', link)
            title = m[1]
            title = re.sub(r'&amp;', '&', title)
            resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    main()
