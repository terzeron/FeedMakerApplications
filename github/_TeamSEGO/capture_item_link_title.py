#!/usr/bin/env python


import os
import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    state = 0
    
    numOfRecentFeeds = 10
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)
    
    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        if state == 0:
            m1 = re.search(r'"path"\s*:\s*"(?P<prefix>[^"]+)"', line)
            if m1:
                prefix = m1.group("prefix")
                state = 1
        elif state == 1:
            m2 = re.search(r'{"name"\s*:\s*"(?P<link>\d[^"]+.md)"}', line)
            if m2:
                link = "http://teamsego.github.io/github-trend-kr/" + prefix + "/" + m2.group("link")
                title = m2.group("link")
                resultList.append((link, title))
            m3 = re.search(r'{"volume":', line)
            if m3:
                lineList.insert(0, line)
                state = 0
        #print(state, end=' ')

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))

if __name__ == "__main__":
    main()
