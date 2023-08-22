#!/usr/bin/env python


import io
import os
import sys
import re
from bin.feed_maker_util import IO


def main():
    state = 0
    num_of_recent_feeds = 1000
    result_list = []
    
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<div class="board_cont"', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)">', line)
            if m:
                link = m.group("link")
                state = 2
        elif state == 2:
            m = re.search(r'<strong class="tit">(?P<title>.*)</strong>', line)
            if m:
                title = m.group("title")
                state = 3
        elif state == 3:
            m = re.search(r'<em class="date">(?P<date>\d+\.\d+\.\d+)\s*<', line)
            if m:
                date = m.group("date")
                title = date + " " + title
                result_list.append((link, title))
                state = 0
            
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
