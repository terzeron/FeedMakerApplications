#!/usr/bin/env python


import sys
import json
import getopt
from bin.feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://brunch.co.kr/@"

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    content = IO.read_stdin()
    json_data = json.loads(content)
    if json_data:
        if "data" in json_data:
            if "list" in json_data["data"]:
                for item in json_data["data"]["list"]:
                    link = url_prefix + item["user"]["profileId"] + "/" + str(item["article"]["no"])
                    title = item["article"]["title"]
                    result_list.append((link, title))


    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
