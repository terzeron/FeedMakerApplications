#!/usr/bin/env python


import sys
import re
from feed_maker_util import IO
import getopt


def main():
    link = ""
    title = ""
    url_prefix = "http://comic.naver.com/"

    num_of_recent_feeds = 1000
    count = 0
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
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
            result_list.append((link, title))

    for (link, title) in result_list[-num_of_recent_feeds:]:
        print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
