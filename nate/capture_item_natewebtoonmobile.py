#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    episodeNum = ""
    title = ""
    state = 0
    urlPrefix = "http://comics.nate.com"

    for line in feedmakerutil.readStdinAsLineList():
        if state == 0:
            m = re.search(r'<a href="(?P<url>/webtoon/detail\.php\?[^"]+)&ampcategory=\d+">', line)
            if m:
                state = 1
                url = urlPrefix + m.group("url")
                link = re.sub(r'&amp;', '&', url)
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
