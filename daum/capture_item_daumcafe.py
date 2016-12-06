#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
import feedmakerutil

def main():
    linkPrefix = "http://cafe.daum.net/_c21_/"
    link = ""
    title = ""
    cafeName = ""
    cafeId = ""
    boardName = ""
    state = 0

    numOfRecentFeeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = feedmakerutil.readStdinAsLineList()
    resultList = []
    for line in lineList:
        if state == 0:
            m = re.search(r'GRPCODE\s*:\s*"(?P<cafeName>[^"]+)"', line)
            if m:
                cafeName = m.group("cafeName")
            m = re.search(r'GRPID\s*:\s*"(?P<cafeId>[^"]+)"', line)
            if m:
                cafeId = m.group("cafeId")
            m = re.search(r'FLDID\s*:\s*"(?P<boardName>[^"]+)"', line)
            if m:
                boardName = m.group("boardName")
            if cafeName != "" and cafeId != "" and boardName != "":
                state = 1
        elif state == 1:
            m = re.search(r'<a[^>]*href="[^"]+/bbs_read[^"]*datanum=(?P<articleId>\d+)[^>]*>(?P<title>.+)</a>', line)
            if m:
                link = linkPrefix + "bbs_read?" + "&fldid=" + boardName + "&grpid=" + cafeId + "&datanum=" + m.group("articleId")
                title = m.group("title")
                title = re.sub(r'(<[^>]*?>|^\s+|\s+$)', '', title)
                if link and title:
                    resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    main()
