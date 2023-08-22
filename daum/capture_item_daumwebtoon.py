#!/usr/bin/env python

import sys
import json
import getopt
import feed_maker_util
from bin.feed_maker_util import IO


def main():
    link_prefix = "http://cartoon.media.daum.net/m/webtoon/viewer/"
    link = ""
    title = ""
    nickname = ""

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    content = IO.read_stdin()
    result_list = []
    json_data = json.loads(content)
    if "data" in json_data:
        if "webtoon" in json_data["data"]:
            if "webtoonEpisodes" in json_data["data"]["webtoon"]:
                for episode in json_data["data"]["webtoon"]["webtoonEpisodes"]:
                    if "price" in episode and episode["price"] > 0:
                        continue
                        
                    if "title" in episode:
                        title = episode["title"]
                    if "articleId" in episode:
                        link = link_prefix + str(episode["articleId"])
                    if title and link:
                        result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))
                

if __name__ == "__main__":
    sys.exit(main())
