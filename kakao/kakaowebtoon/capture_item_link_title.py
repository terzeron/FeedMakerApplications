#!/usr/bin/env python3


import sys
import re
from feedmakerutil import IO


def main():
    link = ""
    title = ""
    num = ""
    state = 0
    url_prefix = "http://page.kakao.com"

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<a href="(?P<link>/home/\d+)\?[^"]+">', line)
            if m:
                link = url_prefix + m.group("link")
                state = 1
        elif state == 1:
            if re.search(r'<p class="ellipsis"', line):
                state = 2
        elif state == 2:
            m = re.search(r'^\s*(?P<title>\S.*\S)\s*$', line)
            if m:
                title = m.group("title")
                print("%s\t%s" % (link, title))
                state = 3
        elif state == 3:
            m = re.search(r'^\s*</p>\s*$', line)
            if m:
                state = 0


if __name__ == "__main__":
    sys.exit(main())
