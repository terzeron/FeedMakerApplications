#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = "http://sports.news.naver.com"

    for line in feedmakerutil.readStdinAsLineList():
        m = re.search(r'<a href="(?P<url>/magazineS/index\.nhn\?id=\d+)">(?P<title>[^<]+)</a>', line)
        if m:
            link = urlPrefix + m.group("url")
            title = m.group("title")
            print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
