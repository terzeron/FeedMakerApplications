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

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        p = re.compile(r'"id":(?P<id>\d+),"episode":(?P<episode>\d+),"title":"(?P<title>[^"]+)",')
        for m in p.finditer(line):
            md = m.groupdict()
            id = md['id']
            episode = int(md['episode'])
            title = md['title']
            title = re.sub(r'\\u0027', '\'', title)
            link = link_prefix + id
            title = "%04d. %s" % (episode, title)
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    sys.exit(main())
