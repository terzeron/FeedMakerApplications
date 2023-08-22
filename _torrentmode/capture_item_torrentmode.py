#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main() -> int:
    url_prefix: str = ""
    link: str = ""
    title: str = ""
    state: int = 0

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        #print(state)
        if state == 0:
            m = re.search(r'<td class="list-subject', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"&\?]+)([^>]+)?">', line)
            if m:
                link = url_prefix + m.group("link")
                state = 2
        elif state == 2:
            m = re.search(r'<span', line)
            if m:
                continue
            m = re.search(r'^(?P<title>.+)(\s*</a>)$', line)
            if m:
                title = m.group("title")
                title = re.sub(r'</?\w+( \w+="[^"]+")*>', '', title)
                if link and title:
                    result_list.append((link, title))
                    state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
