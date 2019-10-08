#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://wfwf43.com"
    state = 0
    
    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<a(?:[^>]*)href="(?P<link>/view[^"]*)&amp;title=[^"]*"', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                state = 1
        elif state == 1:
            m = re.search(r'<div class="subject">\s*(?P<title>[^<]+)\s*</div>', line)
            if m:
                title = m.group("title")
                title = re.sub(r"\s+", " ", title)
                title = re.sub(r'&nbsp;', ' ', title)
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
