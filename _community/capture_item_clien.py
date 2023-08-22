#!/usr/bin/env python

import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    link_prefix = "https://www.clien.net"
    link = ""
    title = ""
    state = 0

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<a class="list_subject"[^>]*href="(?P<url>[^"]+)">', line)
            if m:
                url = m.group("url")
                url = re.sub(r'&amp;', '&', url)
                link = link_prefix + url
                state = 1
        elif state == 1:
            m = re.search(r'<span data-role="list-title-text">(?P<title>.*)</span>', line)
            if m:
                title = m.group("title")
                title = re.sub(r'\s\s+', ' ', title)
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[-num_of_recent_feeds:]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
