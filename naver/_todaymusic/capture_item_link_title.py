#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    state = 0
    resultList = []
    urlPrefix = "http://music.naver.com"
    
    for line in feedmakerutil.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<a\s+class="[^"]+"\s+href=\"(?P<url>/todayMusic/index\.nhn[^\"]+)\"[^>]*>', line)
            if m:
                link = urlPrefix + m.group("url")
                link = re.sub(r'&amp;', '&', link)
                state = 1
        elif state == 1:
            m = re.search(r'<span\s+class="[^"]+"\s+title=\"[^\"]+\"[^>]*>(?P<title>[^<]+)</span>', line)
            if m:
                title = m.group("title")
                resultList.append((link, title))
                state = 0
                        
    count = 0
    for link, title in resultList:
        print("%s\t%s" % (link, title))
        count += 1
        if count >= 7:
            break
            

if __name__ == "__main__":
    sys.exit(main())
