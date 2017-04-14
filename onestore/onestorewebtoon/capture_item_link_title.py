#!/usr/bin/env python3


import sys
import re
import getopt
import feedmakerutil


def main():
    link = ""
    title = ""
    state = 0
    resultList = []
    urlPrefix = "http://m.tstore.co.kr/mobilepoc"

    numOfRecentFeeds = 20
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
        
    for line in feedmakerutil.readStdinAsLineList():
        if state == 0:
            m = re.search(r'''
            <a
            [^>]*
            goInnerUrlDetail\(
            \\
            '
            (?P<url>/webtoon/webtoonList[^']+)
            \\
            ''', line, re.VERBOSE)
            if m:
                link = urlPrefix + m.group("url")
                link = re.sub(r'&amp;', '&', link)
                state = 1
        elif state == 1:
            m = re.search(r'''
            <dt>
            (?P<title>.+)
            </dt>
            ''', line, re.VERBOSE)
            if m:
                title = m.group("title")
                resultList.append((link, title))
                state = 0
                    
    for link, title in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))
        

if __name__ == "__main__":
    sys.exit(main())
