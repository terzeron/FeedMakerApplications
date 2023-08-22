#!/usr/bin/env python


import sys
import re
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    resultList = []
    urlPrefix = "http://music.naver.com"
    
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'<a href="(?P<url>/todayMusic/index\.nhn[^\"]+)"[^>]*>(?P<title>.+)</a>', line)
        if m:
            link = urlPrefix + m.group("url")
            link = re.sub(r'&amp;', '&', link)
            title = m.group("title")
            resultList.append((link, title))
                        
    for link, title in resultList:
        print("%s\t%s" % (link, title))
            

if __name__ == "__main__":
    sys.exit(main())
