#!/usr/bin/env python3


import io
import os
import sys
import re
from feed_maker_util import IO


def main():
    state = 0
    num_of_recent_feeds = 1000
    url_prefix = "https://graphql-kr.github.io"
    result_list = []
    
    for line in IO.read_stdin_as_line_list():
        matches = re.findall('''
        <li>
        <a[^>]*href="(?P<link>[^"]*)"[^>]*>
        (?P<title>[^<]+)
        </a>
        ''', line, re.VERBOSE)
        index = 0
        for match in matches:
            link = url_prefix + match[0]
            title = match[1]
            title = re.sub(r'&amp;', '&', title)
            if re.search(r'#$', link):
                link = link + title
            result_list.append((link, title, index))
            index = index + 1
            
    for (link, title, index) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, index, title))

            
if __name__ == "__main__":
    sys.exit(main())
