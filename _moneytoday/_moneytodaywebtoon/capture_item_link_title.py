#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    icon = ""
    state = 0
    urlPrefix = "http://comic.mt.co.kr/"

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<p class="img2"><a href="./(?P<url>comicDetail.htm\?nComicSeq=\d+)">', line)
            if m:
                link = urlPrefix + m.group("url")
                link = re.sub(r'&amp', '&', link)
                state = 1
        elif state == 1:
            m = re.search(r'<p class="title"><strong>(?P<title>.+)</strong></p>', line)
            if m:
                title = m.group("title")
                print("%s\t%s" % (link, title))
                state = 0

if __name__ == "__main__":
    sys.exit(main())
