#!/usr/bin/env python3


import sys
import re
from feedmakerutil import IO

    
def main():
    link = ""
    urlPrefix = "http://terms.naver.com/"
    title = ""
    state = 0

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<strong class="title">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="/(?P<url>entry\.nhn\?[^"]+)">(?P<title>[^<]+)</a>', line)
            if m:
                url = m.group("url")
                url = re.sub(r'&amp;', '&', url)
                title = m.group("title")
                link = urlPrefix + url
                print("%s\t%s" % (link, title))
                state = 0

            
if __name__ == "__main__":
    sys.exit(main())
