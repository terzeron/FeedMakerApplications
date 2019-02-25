#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
import collections
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = ""
    
    num_of_recent_feeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    list = IO.read_stdin_as_line_list()

    state = 0
    for line in list:
        if state == 0:
            m = re.search(r'href="(?P<url_prefix>https?://[^"/]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<article_id>/\d+)" class="link_post">', line)
            if m:
                link = url_prefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(r'<strong class="tit_post">(?P<title>.+)</strong>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    state = 0
    for line in list:
        if state == 0:
            m = re.search(r'href="(?P<url_prefix>https?://[^"/]+\.tistory\.com)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<h2><a href="(?P<article_id>/\d+)">(?P<title>.*?)</a></h2>', line)
            if m:
                link = url_prefix + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))

    state = 0
    for line in list:
        if state == 0:
            m = re.search(r'url: "(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<h2 class="title"><a href="(?P<link>[^"]+)">(?P<title>.*)</a>', line)
            if m:
                link = url_prefix + m.group("link")
                title = m.group("title")
                result_list.append((link, title))
        
    state = 0
    for line in list:
        if state == 0:
            m = re.search(r'url: "(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<url>/[^"]+)">', line)
            if m:
                link = url_prefix + m.group("url")
                state = 2
        elif state == 2:
            m = re.search(r'<span class="title">(?P<title>.*?)</span>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
        
