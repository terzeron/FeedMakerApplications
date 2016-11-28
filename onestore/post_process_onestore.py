#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():
    imgUrlPrefix = ""
    imgIndex = ""
    imgExt = ""

    for line in feedmakerutil.readStdinAsLineList():
        m = re.search(r"<img src='(?P<urlPrefix>http://m.tstore.co.kr/SMILE_DATA[^']+\/)(?P<index>\d+)\.(?P<ext>jpg)'[^>]*/>", line)
        if m:
            imgUrlPrefix = m.group("urlPrefix")
            imgIndex = int(m.group("index"))
            imgExt = m.group("ext")
            print("<img src='%s%d.%s' width='100%%'/>" % (imgUrlPrefix, imgIndex, imgExt))
            

if __name__ == "__main__":
    sys.exit(main())
