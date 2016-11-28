#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    icon = ""
    urlPrefix = "http://news.naver.com"

    for line in feedmakerutil.readStdinAsLineList():
        m = re.search(r'<a\s+class="[^"]+"\s+href="(?P<url>/main/magazinec/index\.nhn\?componentId=\d+)"', line)
        if m:
            link = urlPrefix + m.group("url")
        elif line =~ m!<strong class="vol">(?P<title>[^<]+)</strong>!:
            title = m.group("title")
        elif line =~ m!<strong class="tit">([^<]+)</strong>!:
            print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
