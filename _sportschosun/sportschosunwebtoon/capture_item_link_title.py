#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    link = ""
    title = ""
    urlPrefix = "http://sports.chosun.com/cartoon/sub_list.htm?title="
  
    for line in feedmakerutil.read_stdin_as_line_list():
        m = re.search(r'<li><a href="[^"]*title=(?P<url>[^"&]+)[^"]*"><img alt="(?P<title>[^"]+)"', line)
        if m:
            if m.group("title") == "coin":
                # 오늘의운세는 skip
                continue
            link = urlPrefix + m.group("url")
            title = m.group("title")
            link = re.sub(r'&amp;', '&', link)
            print("%s\t%s" % (link, title))
            
            
if __name__ == "__main__":
    sys.exit(main())
