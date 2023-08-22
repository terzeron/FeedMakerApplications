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
            m = re.search(r'<ul class="page-list"', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a\s+href="(?P<link>http[^"]+html)"\s+class="[^"]+"\s+title="[^"]+"[^>]*>(?P<title>.+)</a>', line)
            if m:
                link = url_prefix + m.group("link")
                title = m.group("title")
                result_list.append((link, title))

            m = re.search(r'</ul>', line)
            if m:
                break

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
