#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
  
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'<strong><a href="(?P<url>http://sports.khan.co.kr/comics/cartoon_view.html\?comics=b2c&amp;sec_id=\d+)">(?P<title>[^<]+)</a></strong>', line)
        if m:
            link = m.group("url")
            title = m.group("title")
            link = re.sub(r'&amp;', '&', link)
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
