#!/usr/bin/env python3


import os
import sys
import re
import feedmakerutil


def main(url):
    cmd = "markdown"
    html = feedmakerutil.execCmd(cmd)
    #html = re.sub(r'(?P<url>https?://[^"\'\<\>\)\(]+)', r'<a href="\g<url>">\g<url></a>', html)
    #html = re.sub(r'<img src="(?P<imgUrl>[^"]+)"', r'<img src="http://teamsego.github.io/github-trend-kr/\g<imgUrl>"', html)
    print(html)
    

if __name__ == "__main__":
    main(sys.argv[1])
