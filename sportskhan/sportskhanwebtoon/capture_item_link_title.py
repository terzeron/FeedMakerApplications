#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
  
    for line in feedmakerutil.readStdinAsLineList():
        m = re.search(r'<strong><a href="(?P<url>http://sports.khan.co.kr/comics/cartoon_view.html\?comics=b2c&amp;sec_id=\d+)">(?P<title>[^<]+)</a></strong>', line)
        if m:
            link = m.group("url")
            title = m.group("title")
            link = re.sub(r'&amp;', '&', link)
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
