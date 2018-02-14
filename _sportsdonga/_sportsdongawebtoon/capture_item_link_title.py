#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = "http://sports.donga.com/cartoon"

    for line in feedmakerutil.read_stdin_as_line_list():
        m = re.search(r'<li(?: class="first")?><a href="(?P<url>\?cid=[^"]+)"><img alt="(?P<title>[^"]+)"', line)
        if m:
            link = urlPrefix + m.group("url")
            title = m.group("title")
            print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
