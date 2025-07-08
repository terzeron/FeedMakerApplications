#!/usr/bin/env python


import sys
import getopt
import json
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://cafe.naver.com/f-e/cafes/10503958/articles/"

    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    content = IO.read_stdin()
    data = json.loads(content)
    if "result" in data:
        if "articleList" in data["result"]:
            article_list = data["result"]["articleList"]
            for article in article_list:
                if "item" in article:
                    item = article["item"]
                    link = str(item["articleId"])
                    title = item["writerInfo"]["nickName"].rstrip() + ": " + item["subject"].rstrip()
                result_list.append((link, title))
        

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (url_prefix + link, title))


if __name__ == "__main__":
    sys.exit(main())
