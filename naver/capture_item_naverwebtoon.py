#!/usr/bin/env python3


import sys
import re
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "http://comic.naver.com/"

    for line in IO.read_stdin_as_line_list():
        m = re.search(r'''
        <a
        \s+
        href="/
        (?P<url>
        (?:
        webtoon
        |
        challenge
        |
        bestChallenge
        )
        /detail\.nhn
        [^"]*
        no=(?P<title1>\d+)
        [^"]*
        )
        "
        [^>]*
        >
        (?P<title2>.+)
        </a>
        ''', line, re.VERBOSE)
        if m:
            url = m.group("url")
            if re.search(r'no=\d+IBUS', url):
                continue
            url = re.sub("&amp;", "&", url)
            url = re.sub(r"&week(day)?=\w\w\w", "", url)
            link = url_prefix + url
            title = "%04d. %s" % (int(m.group("title1")), m.group("title2"))
            print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
