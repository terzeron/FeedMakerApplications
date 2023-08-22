#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    urlPrefix = "http://sports.news.naver.com"

    for line in IO.read_stdin_as_line_list():
        m = re.search(r'<a href="(?P<url>/magazineS/index\.nhn\?id=\d+)">(?P<title>[^<]+)</a>', line)
        if m:
            link = urlPrefix + m.group("url")
            title = m.group("title")
            print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
