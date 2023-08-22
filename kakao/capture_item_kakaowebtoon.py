#!/usr/bin/env python

import sys
import re
import json
import getopt
from bin.feed_maker_util import IO


def main():
    link_prefix = "https://webtoon.kakao.com/viewer"
    link = ""
    title = ""

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    content = IO.read_stdin()
    content = re.sub(r'(^(<\S[^>]*>)+|(<\S[^>]*>)+$)', '', content)
    result_list = []
    json_data = json.loads(content)
    if "data" in json_data:
        if "episodes" in json_data["data"]:
            for episode in json_data["data"]["episodes"]:
                if not episode["adult"] and episode["useType"] == "FREE":
                    link = "%s/%s/%s" % (link_prefix, episode["seoId"], episode["id"])
                    title = "%s. %s" % (episode["no"], episode["title"])
                    result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
