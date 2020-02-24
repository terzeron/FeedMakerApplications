#!/usr/bin/env python


import io
import os
import sys
import re
from feed_maker_util import IO


def main():
    state = 0
    num_of_recent_feeds = 1000
    url_prefix = "https://kotlinlang.org"
    result_list = []
    
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<a class="tree-item-title[^"]*" href="(?P<link>[^"]+)">', line)
            if m:
                link = url_prefix + m.group("link")
                state = 1
        elif state == 1:
            m = re.search(r'<span class="text">(?P<title>.+)</span>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 0

    num = 1
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d %s" % (link, num, title))
        num = num + 1

            
if __name__ == "__main__":
    sys.exit(main())
