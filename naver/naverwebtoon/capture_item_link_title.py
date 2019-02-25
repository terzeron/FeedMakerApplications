#!/usr/bin/env python3


import sys
import re
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    state = 0
    urlPrefix = "http://comic.naver.com"

    for line in IO.read_stdin_as_line_list():
        m = re.search(r'<a[^>]*href="(?P<url>/webtoon/list.nhn\?titleId=\d+)[^"]*"[^>]*title="(?P<title>[^"]+)"[^>]*/?>', line)
        if m:
            url = m.group("url")
            title = m.group("title")
            link = urlPrefix + url
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
