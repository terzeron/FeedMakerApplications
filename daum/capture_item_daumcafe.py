#!/usr/bin/env python

import io
import os
import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    link_prefix = "http://cafe.daum.net/_c21_/"
    link = ""
    title = ""
    cafe_name = ""
    cafe_id = ""
    board_name = ""
    state = 0

    num_of_recent_feeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'GRPCODE\s*:\s*"(?P<cafe_name>[^"]+)"', line)
            if m:
                cafe_name = m.group("cafe_name")
            m = re.search(r'GRPID\s*:\s*"(?P<cafe_id>[^"]+)"', line)
            if m:
                cafe_id = m.group("cafe_id")
            m = re.search(r'FLDID\s*:\s*"(?P<board_name>[^"]+)"', line)
            if m:
                board_name = m.group("board_name")
            if cafe_name != "" and cafe_id != "" and board_name != "":
                state = 1
        elif state == 1:
            m = re.search(r'<a[^>]*href="[^"]+/bbs_read[^"]*datanum=(?P<article_id>\d+)[^>]*>(?P<title>.+)</a>', line)
            if m:
                link = link_prefix + "bbs_read?" + "&fldid=" + board_name + "&grpid=" + cafe_id + "&datanum=" + m.group("article_id")
                title = m.group("title")
                title = re.sub(r'(<[^>]*?>|^\s+|\s+$)', '', title)
                if link and title:
                    result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    sys.exit(main())
