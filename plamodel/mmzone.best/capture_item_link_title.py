#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO

def main():
    state = 0
    url_prefix = "https://mmzone.co.kr"
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<div class="gallery-title">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<div>(?P<title>.+)</div>', line)
            if m:
                title = m.group("title")
                state = 2
        elif state == 2:
            m = re.search('<a href="(?P<link>[^"]+)"[^>]*>', line)
            if m:
                link = url_prefix + m.group("link")
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
