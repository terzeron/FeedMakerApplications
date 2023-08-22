#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def print_usage():
    print("usage:\t%s [ -n <limit of recent feeds> ]\n" % (sys.argv[0]))
    sys.exit(-1)


def main():
    link = ""
    title = ""
    resultList = []
    urlPrefix = "http://stoo.asiae.co.kr/cartoon/ctview.htm?"

    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    for line in IO.read_stdin_as_line_list():
        m = re.search(r'<a href="/cartoon/ctview.htm[^"]*(?P<url>id=[^&]+)[^"]*"[^>]*><span>(?P<title>.*)</span></a>', line)
        if m:
            title = m.group("title")
            link = urlPrefix + m.group("url")
            link = re.sub(r'&amp;', '&', link)
            resultList.append((link, title))


    for link, title in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))

if __name__ == "__main__":
    sys.exit(main())
