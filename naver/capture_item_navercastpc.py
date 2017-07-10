#!/usr/bin/env python3


import sys
import re
import feedmakerutil

    
def main():
    link = ""
    urlPrefix = "http://terms.naver.com/"
    title = ""

    for line in feedmakerutil.readStdinAsLineList():
        m = re.search (r'<dt><a href="/(?P<url>entry\.nhn\?[^"]+)"><strong>(?P<title>[^<]+)</strong></a>', line)
        if m:
            url = m.group("url")
            url = re.sub(r'&amp;', '&', url)
            title = m.group("title")
            link = urlPrefix + url
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
