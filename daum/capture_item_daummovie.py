#!/usr/bin/env python3


import sys
import re
import feedmakerutil

def main():
    link = ""
    title = ""
    linkPrefix = "http://movie.daum.net/movieinfo/news/"

    for line in feedmakerutil.readStdinAsLineList():
        m = re.search(r"<h5><a\s+class=\"[^\"]+\"\s+href=\"(?P<link>movieInfoArticleRead\.do[^\"]+)\"[^>]*>(?P<title>.+)</a></h5>", line)
        if m:
            link = linkPrefix + m.group("link")
            link = re.sub(r"&amp;", "&", link)
            title = m.group("title")
            print("%s\t%s" % (link, title))

if __name__ == "__main__":
    sys.exit(main())
