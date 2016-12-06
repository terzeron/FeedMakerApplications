#!/usr/bin/env python3


import sys
import re
import getopt
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = "http://m.tstore.co.kr/mobilepoc/webtoon/webtoonDetail.omp?prodId="
    resultList = []

    numOfRecentFeeds = 1000
    count = 0
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    for line in feedmakerutil.readStdinAsLineList():
        matches = re.findall(r'''
        [^}]*,
        "prodId"\s*:\s*"\s*([^"]+)\s*",
        [^}]*,
        "prodNm"\s*:\s*"\s*([^"]+)\s*",
        ''', line, re.VERBOSE)
        for match in matches:
            link = urlPrefix + match[0]
            title = match[1]
            if link and title:
                resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))

if __name__ == "__main__":
    sys.exit(main())
