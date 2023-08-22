#!/usr/bin/env python


import os
import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    link_prefix = "https://newstapa.org"

    num_of_recent_feeds = 10
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        matches = re.findall(r'''
        <h\d\s+class="[^"]+">
        <a\s+href="(?P<link>/article/[^"]+)">
        (?P<title>[^<]+)
        </a>
        </h\d>
        <p\s+class="[^"]+ date">
        (?P<date>\d+\.\d+\.\d+)
        </p>
        ''', line, re.VERBOSE)
        for match in matches:
            link = link_prefix + match[0]
            title = match[1]
            article_date = match[2]
            result_list.append((link, title, article_date))

    for (link, title, article_date) in result_list[:num_of_recent_feeds]:
        print("%s\t%s %s" % (link, article_date, title))


if __name__ == "__main__":
    sys.exit(main())
