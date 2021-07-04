#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO, URL


def main() -> int:
    link: str = ""
    title: str = ""
    url_prefix = ""
    state = 0

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<meta\s+property="og:url"\s+content="(?P<url_prefix>http[^"]+)"\s*/?>', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div class="num">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'<td[^>]*title="(?P<title>[^"]+)">', line)
            if m:
                title = m.group("title")
                state = 3
        elif state == 3:
            m = re.search(r'<a href="(?P<link>[^"]+)">', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                link = URL.concatenate_url(url_prefix, link)
                result_list.append((link, title))
                state = 1

    num = len(result_list)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num - 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
