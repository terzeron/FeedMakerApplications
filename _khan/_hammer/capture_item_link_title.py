#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    link_prefix = "http://news.khan.co.kr/kh_cartoon/"

    num_of_recent_feeds = 10
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        m1 = re.search(r'<a href=["\']\./(?P<link>khan_index\.html\?artid=\d+)[^"\']*["\']>(?P<title>[^<]+)</a>', line)
        if m1:
            link = link_prefix + m1.group("link")
            title = m1.group("title")
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
