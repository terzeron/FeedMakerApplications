#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = ""

    num_of_recent_feeds = 2000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    html = IO.read_stdin_as_line_list()

    state = 0
    for line in html:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<article_id>/\d+)(?:\?category=\d+)?" class="link_post">', line)
            if m:
                link = url_prefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(r'<strong class="tit_post\s*">(?P<title>.+)</strong>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    state = 0
    for line in html:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^"]+)"', line)
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
    for line in html:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<h2 class="title"><a href="(?P<article_id>\d+)">(?P<title>.*)</a>', line)
            if m:
                link = url_prefix + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))

    state = 0
    for line in html:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<article_id>/\d+)(?:\?category=\d+)?">', line)
            if m:
                link = url_prefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(r'<span class="title">(?P<title>.*?)</span>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    state = 0
    for line in html:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<li><a href="(?P<article_id>[^"\?]+)(?:\?category=\d+)?">', line)
            if m:
                link = url_prefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(r'<strong class="tit_blog"[^>]*>(?P<title>.*?)</strong>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    state = 0
    for line in html:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^"]+)"', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div id="body" class="list">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'<div id="body" class="entry">', line)
            if m:
                # 본문 시작이면 종료
                break

            m = re.search(r'<a href="(?P<article_id>/entry/[^"?=]+)(?:\?category=\d+)?">(?P<title>.+)</a>', line)
            if m:
                link = url_prefix + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))
                state = 2

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
