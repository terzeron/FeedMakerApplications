#!/usr/bin/env python


import sys
import re
import getopt
from typing import List, Tuple
from feed_maker_util import IO


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
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https://torrentdia[^"]+\.com)/[^"]*"/>', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<td class="\s*list-subject', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'^\s*<a href="https?://torrentdia\d+\.com(?P<link>[^"]*wr_id=\d+[^"]*)"[^>]*>\s*(?P<title>\S.+)\s*</a>$', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                title = m.group("title")
                title = re.sub(r'</?\w+( \w+="[^"]+")*>', '', title)
                if "보증업체" not in title and "보증제휴" not in title and "타 사이트 워터마크" not in title and "삭제" not in title and "신고누적으로 블라인드" not in title:
                    result_list.append((link, title))
                state = 1
            else:
                m = re.search(r'^\s*<a href="https?://torrentdia\d+\.com(?P<link>[^"]*wr_id=\d+[^"]*)"[^>]*>', line)
                if m:
                    link = url_prefix + m.group("link")
                    link = re.sub(r'&amp;', '&', link)
                    state = 3
        elif state == 3:
            m = re.search(r'\s*(?P<title>\S.+)\s*</a>$', line)
            if m:
                title = m.group("title")
                title = re.sub(r'</?\w+( \w+="[^"]+")*>', '', title)
                if "보증업체" not in title and "보증제휴" not in title and "타 사이트 워터마크" not in title and "삭제" not in title:
                    result_list.append((link, title))
                state = 1

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
