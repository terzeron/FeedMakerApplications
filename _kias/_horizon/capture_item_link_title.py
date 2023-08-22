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
            m = re.search(r'<article[^>]*id="post-(?P<id>\d+)"', line)
            if m:
                id = int(m.group("id"))
                state = 1
        elif state == 1:
            m = re.search(r'<header class="post-title', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'<a href="(?P<link>[^"]+)"[^>]*title="(?P<title>[^"]+)">', line)
            if m:
                link = m.group("link")
                title = m.group("title")
                result_list.append((link, title, id))
                state = 0
            
    for (link, title, index) in result_list[:num_of_recent_feeds]:
        print("%s\t%d. %s" % (link, id, title))

            
if __name__ == "__main__":
    sys.exit(main())
