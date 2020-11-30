#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO


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
            m = re.search(r'var\s+g5_url\s+=\s+"(?P<url_prefix>[^"]+)";', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<td[^>]*name="view_list"[^>]*data-role="(?P<link>[^"]+)">', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                link = url_prefix + link
                state = 2
        elif state == 2:
            m = re.search(r'<td[^>]*class="content__title"', line)
            if m:
                state = 3
        elif state == 3:
            m = re.search(r'\s*(?P<title>\S[^<>]*)(?:</td>)?\s*', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    num = len(result_list)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num - 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
