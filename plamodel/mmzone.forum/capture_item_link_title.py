#!/usr/bin/env python


import os
import sys
import re
import getopt
from bin.feed_maker_util import IO

def main():
    state = 0
    url_prefix_for_forum = "http://mmzone.co.kr/mms_tool/"
    url_prefix_for_album = "http://mmzone.co.kr/album/"
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<div id="title" class="ELLIPSIS"', line)
            if m:
                state = 1

            m = re.search(r'<a href="(?P<link>[^"]+no=\d+)&[^"]+">(?P<title>.+)</a>', line)
            if m:
                if m.group("link").startswith("javascript"):
                    continue
                link = url_prefix_for_forum + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                title = m.group("title")
                result_list.append((link, title))

            m = re.search(r'<div id="scm_thumb_frame".*onclick="javascript:location.href=\'(?P<link>[^\']+)\'"', line)
            if m:
                link = url_prefix_for_album + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                state = 1
                
        elif state == 1:
            m = re.search(r'<div id="scm_info_title">(?P<title>.+)</div>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 0

            m = re.search(r'onclick="location.href=\'(?P<link>[^"]+no=\d+)&[^"]+\'"[^>]*>(?P<title>.+)</div>', line)
            if m:
                if m.group("link").startswith("javascript"):
                    continue
                link = url_prefix_for_forum + m.group("link")
                link = re.sub(r'&amp;', '&', link)
                title = m.group("title")
                result_list.append((link, title))
                state = 0

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
