#!/usr/bin/env python


import sys
import json
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://sisain.co.kr/news/articleView.html?idxno="

    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list: List[Tuple[str, str]] = []
    content = IO.read_stdin()
    json_data = json.loads(content)
    if json_data:
        if "data" in json_data:
            for item in json_data["data"]:
                title = item["title"]
                link = url_prefix + item["idxno"]
                result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
