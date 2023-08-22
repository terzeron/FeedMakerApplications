#!/usr/bin/env python


import io
import os
import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    icon = ""
    state = 0

    line_list = IO.read_stdin_as_line_list()
    for line in line_list:
        if state == 0:
            m1 = re.search(r'<a href="(?P<link>[^"]+mag_id=\d+)">', line)
            if m1:
                link = m1.group("link")
                link = re.sub(r'&amp;', '&', link)
                link = "http://www.cine21.com" + link
                state = 1
        elif state == 1:
            m2 = re.search(r'<span class="tit">(?P<title>[^\n\r]+)</span>', line)
            if m2:
                title = m2.group("title")
                if re.search(r'(대학교|영화학|모집)', title):
                    continue
                title = re.sub(r'&lt;', '"', title)
                title = re.sub(r'&gt;', '"', title)
                print("%s\t%s" % (link, title))
                state = 0


if __name__ == "__main__":
    sys.exit(main())
