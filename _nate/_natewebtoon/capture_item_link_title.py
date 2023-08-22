#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    state = 0
    urlPrefix = "http://comics.nate.com"

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<a class="wtl_toon" href="(?P<url>/webtoon/list.php\?btno=\d+)[^"]*">', line)
            if m:
                link = 1
                link = urlPrefix + m.group("url")
                state = 1
        elif state == 1:
            m = re.search(r'<span class="wtl_img"><i></i><img alt="(?P<title>[^"]+)"', line)
            if m:
                title = m.group("title")
                print("%s\t%s" % (link, title))
                state = 0


if __name__ == "__main__":
    sys.exit(main())
