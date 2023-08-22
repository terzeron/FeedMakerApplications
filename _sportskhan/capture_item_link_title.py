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
    url = ""
    cartoonId = 0
    episodeId = 0
    episodeNum = 0
    state = 0
    urlPrefix = "http://sports.khan.co.kr"
    resultList = []

    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
    
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'document\.location\.href\s*=\s*"(?P<url>[^"]+)"', line)
            if m:
                url = m.group("url")
                state = 1
        elif state == 1:
            matches = re.findall(r"<option value='(?P<cartoonId>\d+)\|(?P<episodeId>\d+)(?:\|\d+)?'(?: selected)?>(?P<title>[^<]+)</option>", line)
            for match in matches:
                cartoonId = match[0]
                episodeId = match[1]
                title = match[2]
                link = urlPrefix + url + cartoonId + "&page=" + episodeId
                link = re.sub(r'&amp;', '&', link)
                resultList.append((link, title))

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
                   

if __name__ == "__main__":
    sys.exit(main())
