#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = "http://stoo.asiae.co.kr"

    for line in feedmakerutil.read_stdin_as_line_list():
        m = re.search(r'<a href="(?P<url>/cartoon/list.htm\?sec=\d+)"', line)
        if m:
            url = m.group("url")
            link = re.sub(r'&amp;', '&', link)
            link = urlPrefix + url
        else:
            m = re.search(r'<dt class="desc">(?P<title>[^<]+)</dt>', line)
            if m:
                title = m.group("title")
                print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
