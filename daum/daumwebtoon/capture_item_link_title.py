#!/usr/bin/env python3


import io
import os
import sys
import re
import feedmakerutil


def main():
    lineList = feedmakerutil.readStdinAsLineList()
    for line in lineList:
        matches = re.findall(r'nickname":"([^"]+)"[^}]*"title":"([^"]+)', line)

        for match in matches:
            link = "http://cartoon.media.daum.net/webtoon/view/" + match[0]
            title = match[1]
            print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    main()
        
