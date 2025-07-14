#!/usr/bin/env python


import sys
import re
import getopt
import json
from math import log2
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://m.cafe.naver.com/ca-fe/web/cafes/10503958/articles/"

    num_of_recent_feeds = 30
    threshold = 0.0
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:t:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == '-t':
            threshold = float(a)

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
                    nickname = re.sub(r'\n', '', item["writerInfo"]["nickName"].strip())
                    subject = re.sub(r'\n', '', item["subject"].strip())
                    title = nickname + ": " + subject
                    if threshold > 0.0:
                        # (log(comment)+log(like))/log(read) + log(read)/10
                        score = (log2(int(item["commentCount"]) + 1) + log2(int(item["likeCount"]) + 1)) / log2(int(item["readCount"]) + 1) + log2(int(item["readCount"]) + 1) / 10
                        if score < threshold:
                            continue
                    result_list.append((link, title))
        

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (url_prefix + link, title))


if __name__ == "__main__":
    sys.exit(main())
