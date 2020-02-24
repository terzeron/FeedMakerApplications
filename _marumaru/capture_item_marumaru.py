#!/usr/bin/env python


import io
import os
import sys
import re
import getopt
from feed_maker_util import IO


def main():
    link = ""
    title = ""

    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        matches = re.findall(r'''
        <a
        \s+
        (?:class="[^"]+"\s*)?
        href="
        (?P<link>http://(?!marumaru\.in)[^"]+)
        "
        [^>]*
        >
        (?:<(?:span|font)[^>]*>)*
        (?P<title>(?!</?\w+).*?(?:화|권|부|편)[^<]*)
        (?:</(?:span|font)>)*
        </a>
        ''', line, re.VERBOSE)
        for m in matches:
            link = m[0]
            link = re.sub(r'&amp;', '&', link)
            link = re.sub(r'http://(www.shencomics|www.yuncomics|blog.yuncomics).com', 'http://wasabisyrup.com', link)
            title = m[1]
            title = re.sub(r'&amp;', '&', title)
            title = re.sub(r'&lt;', '<', title)
            title = re.sub(r'&gt;', '>', title)
            resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
