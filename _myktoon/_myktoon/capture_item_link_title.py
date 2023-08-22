#!/usr/bin/env python

import io
import os
import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    count = 0
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    state = 0
    url_prefix = "https://v2.myktoon.com/web/works/"
    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<a href="http.*(?P<url>list.kt\?worksseq=\d+)" class="link">', line)
            if m:
                url = m.group("url")
                state = 1
        elif state == 1:
            m = re.search(r'<strong>(?P<title>.*)</strong>', line)
            if m:
                title = m.group("title")
                link = url_prefix + url
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
	sys.exit(main())

