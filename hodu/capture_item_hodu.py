#!/usr/bin/env python

import io
import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = ""
    num = 0
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
            m = re.search(r'g5_url\s*=\s*"(?P<url_prefix>http[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div\s+class="num">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'^\s*(?P<num>\d+)\s*</div>', line)
            if m:
                num = m.group("num")
                state = 3
        elif state == 3:
            m = re.search(r'<td[^>]*title="(?P<title>[^"]+)">', line)
            if m:
                title = m.group("title")
                title = re.sub(r"\s+", " ", title)
                title = re.sub(r'&nbsp;', ' ', title)
                title = num + ". " + title
                state = 4
        elif state == 4:
            m = re.search(r'<a\s*href="(?P<link>/[^"]*\.html)"', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                result_list.append((link, title))
                state = 1

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
