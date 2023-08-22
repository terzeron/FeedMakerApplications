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
    episodeNum = ""
    state = 0
    urlPrefix = "http://sports.chosun.com/cartoon"
    resultList = []

    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
          
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<li class="section1">(?P<episodeNum>[^<]+)</li>', line)
            if m:
                episodeNum = m.group("episodeNum")
                state = 1
        elif state == 1:
            m = re.search(r'<li class="section2"><a href="(?P<url>[^"]+)">\[[^\]]+\] (?P<title>[^<]+)</a></li>', line)
            if m:
                url = m.group("url")
                title = m.group("title")
                link = re.sub(r'&amp;', '&', link)
                link = urlPrefix + url
                title = episodeNum + " " + title
                resultList.append((link, title))

    for link, title in resultList[-numOfRecentFeeds:]:
          print("%s\t%s" % (link, title))

                        

if __name__ == "__main__":
    sys.exit(main())
