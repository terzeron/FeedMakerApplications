#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    num = ""
    state = 0
    urlPrefix = "http://page.kakao.com/home/"

    for line in feedmakerutil.readStdinAsLineList():
        if state == 0:
            m = re.search(r'<li class="list ajaxCallList\s*" data-seriesid="(?P<seriesId>\d+)">', line)
            if m:
                link = urlPrefix + m.group("seriesId")
                state = 1
        elif state == 1:
            if re.search(r'<dt class="title ellipsis">', line):
                state = 2
        elif state == 2:
            if re.search(r'<img', line):
                continue
            m = re.search(r'^\s*(?P<title>\S.*\S)\s*$', line)
            if m:
                title = m.group("title")
                print("%s\t%s" % (link, title))
                state = 0


if __name__ == "__main__":
    sys.exit(main())
