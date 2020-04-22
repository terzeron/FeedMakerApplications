#!/usr/bin/env python


import io
import os
import sys
import re
import getopt
from feed_maker_util import IO
import typing
from typing import List


def main() -> int:
    link: str = ""
    title: str = ""
    url_prefix: str = ""
    num: int = 0
    state: int = 0

    num_of_recent_feeds: int = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list: List[str] = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'g5_url\s+=\s+"(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<tr\s+[^>]+href=\'(?P<link>/[^\']+\.adulti)\'">', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                state = 2
        elif state == 2:
            m = re.search(r'<div class="episode_subtitle">(?P<title>[^<]+)</div>', line)
            if m:
                title = m.group("title")
                title = re.sub(r"\s+", " ", title)
                result_list.append((link, title))
                state = 1

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
