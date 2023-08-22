#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    episodeNum = ""
    title = ""
    state = 0
    urlPrefix = "http://comics.nate.com"

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<a href="(?P<url>/webtoon/detail\.php\?[^"]+)&amp;category=\d+">', line)
            if m:
                url = urlPrefix + m.group("url")
                link = re.sub(r'&amp;', '&', url)
                state = 1
        elif state == 1:
            m = re.search(r'<span class="tel_episode">(?P<episodeNum>.+)</span>', line)
            if m:
                episodeNum = m.group("episodeNum")
                state = 2
        elif state == 2:
            m = re.search(r'<span class="tel_title">(?P<title>.+)</span>', line)
            if m:
                title = episodeNum + " " + m.group("title")
                print("%s\t%s" % (link, title))
                state = 0


if __name__ == "__main__":
    sys.exit(main())
