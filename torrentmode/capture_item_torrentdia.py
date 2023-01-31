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
            m = re.search(r'<td class="list-subject web-subject', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'^\s*<a[^>]*href="https?://torrentdia\d+\.com(?P<link>[^"]*wr_id=\d+[^"]*)"[^>]*>\s*(?P<title>\S.+)\s*</a>$', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                title = m.group("title")
                title = re.sub(r'</?\w+( \w+="[^"]+")*>', '', title)
                if re.search(r'(\bS\d\dE\d\d\b|\bE\d\d\d?\.\d\d\d\d\d\d\b|보증\s*(업체|제휴)|타\s*사이트\s*워터마크|삭제|블라인드)', title, re.IGNORECASE):
                    link = ""
                    title = ""
                    state = 1
                    continue

                if link and title:
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
                if re.search(r'(\bS\d\dE\d\d\b|\bE\d\d\d?\.\d\d\d\d\d\d\b|보증\s*(업체|제휴)|타\s*사이트\s*워터마크|삭제|블라인드)', title, re.IGNORECASE):
                    title = ""
                    link = ""
                    state = 1
                    continue

                if link and title:
                    result_list.append((link, title))
                    state = 1

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
