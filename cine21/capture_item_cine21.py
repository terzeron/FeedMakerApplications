#!/usr/bin/env python3


import io
import os
import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    icon = ""
    state = 0

    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        if state == 0:
            m1 = re.search(r'<a href="(?P<link>[^"]+)">', line)
            if m1:
                link = m1.group("link")
                link = re.sub(r'&amp;', '&', link)
                link = "http://www.cine21.com" + link
                state = 1
        elif state == 1:
            m2 = re.search(r'<span class="tit">(?P<title>[^<]+)</span>', line)
            if m2:
                title = m2.group("title")
                title = re.sub(r'&lt;', '"', title)
                title = re.sub(r'&gt;', '"', title)
                print("%s\t%s" % (link, title))
                state = 0


if __name__ == "__main__":
    main()
