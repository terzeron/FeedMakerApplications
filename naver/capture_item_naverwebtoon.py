#!/usr/bin/env python


import sys
import re
import getopt
import json
from feed_maker_util import IO, URL


def main():
    link = ""
    title = ""
    url_template = "https://comic.naver.com/webtoon/detail?titleId=%d&no=%d"

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    content = IO.read_stdin()
    data = json.loads(content)
    result_list = []
    if "titleId" in data and data["titleId"]:
        title_id = data["titleId"]
        if "articleList" in data and data["articleList"]:
            article_list = data["articleList"]
            for article in article_list:
                if "no" in article and article["no"]:
                    no = article["no"]
                    link = url_template % (title_id, no)
                if "subtitle" in article and article["subtitle"]:
                    title = article["subtitle"]
                result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
