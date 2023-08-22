#!/usr/bin/env python

import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    clien_link_prefix = "https://www.clien.net"
    mlbpark_link_prefix = "http://mlbpark.donga.com"
    bobaedream_link_prefix = "http://www.bobaedream.co.kr"
    link = ""
    title = ""
    state = 0

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []

    # clien
    for line in line_list:
        if state == 0:
            m = re.search(r'<a class="list_subject"[^>]*href="(?P<url>[^"]+)"', line)
            if m:
                url = m.group("url")
                url = re.sub(r'&amp;', '&', url)
                link = clien_link_prefix + url
                state = 1
        elif state == 1:
            m = re.search(r'<span data-role="list-title-text">(?P<title>.*)</span>', line)
            if m:
                title = m.group("title")
                title = re.sub(r'\s\s+', ' ', title)
                result_list.append((link, title))
                state = 0

    # mlbpark
    for line in line_list:
        matches = re.findall(r'<a alt="[^"]*" class="[^"]*" href="([^"]*id=[^"]*)" title="([^"]+)"', line)
        for match in matches:
            url = match[0]
            url = re.sub(r'&amp;', '&', url)
            title = match[1]
            result_list.append((url, title))

    # bobaedream
    for line in line_list:
        m = re.search(r'<a class="bsubject"[^>]*href="(?P<url>[^"]*bm=1[^"]*)"[^>]*title="(?P<title>[^"]+)"', line)
        if m:
            url = m.group("url")
            url = re.sub(r'&amp;', '&', url)
            link = bobaedream_link_prefix + url
            title = m.group("title")
            result_list.append((link, title))

    for (link, title) in result_list[-num_of_recent_feeds:]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
