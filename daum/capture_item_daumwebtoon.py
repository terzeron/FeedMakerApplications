#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
import feed_maker_util
from feed_maker_util import IO


def main():
    link_prefix = "http://cartoon.media.daum.net/m/webtoon/viewer/"
    link = ""
    title = ""
    nickname = ""

    numOfRecentFeeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = IO.read_stdin_as_line_list()
    resultList = []
    for line in lineList:
        p = re.compile(r'"id":(?P<id>\d+),"episode":(?P<episode>\d+),"title":"(?P<title>[^"]+)",')
        for m in p.finditer(line):
            md = m.groupdict()
            id = md['id']
            episode = int(md['episode'])
            title = md['title']
            link = link_prefix + id
            title = "%04d. %s" % (episode, title)
            resultList.append((link, title))

    for (link, title) in resultList[:numOfRecentFeeds]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    sys.exit(main())
