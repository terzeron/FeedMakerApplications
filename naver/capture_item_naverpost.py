#!/usr/bin/env python3

import io
import os
import sys
import re
import getopt
import json
import feedmakerutil


def main():
    urlPrefix = "http://m.post.naver.com"
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
        #print(html)
        
    state = 0
    resultList = []
    for line in html.split("\n"):
        if state == 0:
            m = re.search(r'<a href="(?P<url>/viewer/postView\.nhn\?volumeNo=\d+&memberNo=\d+)"', line)
            if m:
                url = m.group("url")
                url = re.sub(r'&lt;', '<', url)
                url = re.sub(r'&gt;', '>', url)
                link = urlPrefix + url
                state = 1
        elif state == 1:
            if re.search(r'class="link_end"', line):
                state = 2
            else:
                state = 0
        elif state == 2:
            m = re.search(r'<h3 class="tit_feed', line)
            if m:
                state = 3
            else:
                state = 0
        elif state == 3:
            m = re.search(r'\s*(?P<title>\S+.*\S+)\s*', line)
            if m:
                title = m.group("title")
                if re.search(r'^\s*\[대림자동차\s*공식\s*포스트\]\s*$', title):
                    continue
                title = re.sub(r'^\s+|\s+$', '', title)
                title = re.sub(r'&#39;', '\'', title)
                title = re.sub(r'&#40;', ')', title)
                title = re.sub(r'&#41;', '(', title)
                title = re.sub(r'&lt;', '<', title)
                title = re.sub(r'&gt;', '>', title)
                title = re.sub(r'&nbsp;', ' ', title)
                title = re.sub(r'&quot;', '"', title)
                title = re.sub(r'\[대림자동차\s*공식\s*포스트\]\s*', '', title)
                title = re.sub(r'</h3>', '', title)
                if link and title:
                    resultList.append((link, title))
                state = 0

    for (link, title) in resultList[-numOfRecentFeeds:]:
        print("%s\t%s" % (link, title))
                
                
if __name__ == "__main__":
	main()

