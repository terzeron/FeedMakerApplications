#!/usr/bin/env python3


import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    state = 0
    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<a class="deco" href="(?P<link>[^\?"]+)[^"]*">(?P<title>.+)</a>', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                title = m.group("title")
                state = 1
        elif state == 1:
            m = re.search(r'<a class="nick"[^>]*>\s*ㅣ\s*(?P<author>.*?)\s*</a>', line)
            if m:
                author = m.group("author")
                title = title + " | " + author
                result_list.append((link, title))
                state = 0
                              
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
