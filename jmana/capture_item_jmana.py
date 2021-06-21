#!/usr/bin/env python


#import io
#import os
import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO


def main() -> int:
    url_prefix: str = ""
    link: str = ""
    title: str = ""
    num: int = 0
    state: int = 0

    num_of_recent_feeds: int = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list: List[str] = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^/]+)[^"]*"\s*/?>', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a\s+class="tit[^"]*"[^>]*href="(?P<link>[^"]+bookdetail[^"]+)"[^>]*>(?P<title>.+)</a>', line)
            if m:
                link = url_prefix + m.group("link")
                title = m.group("title")
                link = re.sub(r'&amp;', '&', link)
                link = re.sub(r' ', '+', link)
                title = re.sub(r"\s+", " ", title)
                result_list.append((link, title))

    num = len(result_list)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num - 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
