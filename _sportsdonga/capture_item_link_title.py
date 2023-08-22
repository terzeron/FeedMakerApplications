#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    urlPrefix = ""
    state = 0
    resultList = []
    urlPrefix = ""

    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'window\.location\.href\s*=\s*"(?P<url>[^"]+)"', line)
            if m:
                urlPrefix =  + m.group("url")
                state = 1
        elif state == 1:
            matches = m.findall(r'<option (?:selected="" )?value="(?P<url>\d+)">(?P<title>[^<]+)</option>', line)
            for match in matches:
                link = urlPrefix + match[1]
                title = match[0]
                resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
        

if __name__ == "__main__":
    sys.exit(main())
