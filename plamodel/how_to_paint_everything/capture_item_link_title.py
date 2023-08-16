#!/usr/bin/env python


import os
import sys
import re
import getopt
from feed_maker_util import IO

def main():
    state = 0
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<div class="td-block-row">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)"[^>]*title="(?P<title>[^"]+)" >', line)
            if m:
                link = m.group("link")
                title = m.group("title")
                title = re.sub(r'&#8217;', '\'', title)
                title = re.sub(r'&#8211;', '-', title)
                result_list.append((link, title))

            m = re.search(r'<aside id="media_image', line)
            if m:
                break
                              
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
