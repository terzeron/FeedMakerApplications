#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
import json
import feedmakerutil


def main():
    link_prefix = "http://m.post.naver.com"
    link = ""
    title = ""
    
    numOfRecentFeeds = 1000
    count = 0
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            numOfRecentFeeds = int(a)

    lineList = feedmakerutil.readStdinAsLineList()
    content = "".join(lineList)
    m = re.search(r'"html"\s*:\s*"(?P<html>.*)"\s*}\s*$', content)
    if m:
        html = m.group("html")
        html = re.sub(r'\\r', '', html)
        html = re.sub(r'\\n', '\n', html)
        html = re.sub(r'\\t', '\t', html)
        html = re.sub(r'\\\'', '\'', html)
        html = re.sub(r'\\"', '"', html)
        html = re.sub(r'\\/', '/', html)
        html = re.sub(r'\\x3C', r'<', html)
        html = re.sub(r'\\>', r'>', html)

    state = 0
    resultList = []
    for line in html.split("\n"):
        if state == 0:
            m = re.search(r'<a href="(?P<link>/viewer/postView\.nhn\?volumeNo=\d+&memberNo=\d+)"', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&lt;', '<', link)
                link = re.sub(r'&gt;', '>', link)
                link = link_prefix + link
            m = re.search(r'<h3 class="tit_feed', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'\s*(?P<title>\S+.*)</h3>', line)
            if m:
                title = m.group("title")
                title = re.sub(r'^\s+|\s+$', '', title)
                title = re.sub(r'&#39;', '\'', title)
                title = re.sub(r'&#40;', ')', title)
                title = re.sub(r'&#41;', '(', title)
                title = re.sub(r'\[대림자동차\s*공식\s*포스트\]', '', title)
                resultList.append((link, title))
                state = 0

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
                
                
if __name__ == "__main__":
	main()

