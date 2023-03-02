#!/usr/bin/env python


import sys
import re
import getopt
from feed_maker_util import IO, URL


def main():
    link = ""
    title = ""
    url_prefix = "https://comic.naver.com/"

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        matches = re.findall(r'<a href="([^"]+)" class="EpisodeListList[^"]*">(?:\s*<div[^>]*>)?(?:\s*<img[^>]*>)?(?:\s*</div>)?(?:\s*<div[^>]*>)?(?:\s*<p[^>]*>)?\s*<span class="EpisodeListList[^"]*">\s*(.*?)\s*</span>', line)
        for match in matches:
            url = match[0]
            title = match[1]
            if re.search(r'no=\d+IBUS', url):
                continue
            url = re.sub("&amp;", "&", url)
            url = re.sub(r"&week(day)?=\w\w\w", "", url)
            link = URL.concatenate_url(url_prefix, url)
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
