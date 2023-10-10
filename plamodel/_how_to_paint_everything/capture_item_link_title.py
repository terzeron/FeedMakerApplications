#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO

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
                state = 2
        elif state == 2:
            m = re.search(r'<span class="td-post-date"><time class="entry-date updated td-module-date" datetime="(?P<date>\d+-\d+-\d+)T\d+:\d+:\d+\+\d+:\d+"', line)
            if m:
                date_str = m.group("date")
                title = f"{title} {date_str}"
                result_list.append((link, title))
                state = 1
                              
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
