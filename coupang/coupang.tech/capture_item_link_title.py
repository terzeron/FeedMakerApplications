#!/usr/bin/env python3


import io
import os
import sys
import re
import getopt
import json
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "https://medium.com/coupang-tech/"
    state = 0
    
    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    content = IO.read_stdin()
    result_list = []
    m = re.search(r'<script>//\s*<\!\[CDATA\[\s*window\["obvInit"\]\((?P<script>.*)\)\s*//\s*\]\]></script>', content)
    if m:
        json_content = m.group("script")
        json_data = json.loads(json_content)
        if json_data:
            if "references" in json_data:
                if "Post" in json_data["references"]:
                    for item in json_data["references"]["Post"]:
                        #import pprint
                        #pprint.pprint(json_data["references"]["Post"][item])
                        item_data = json_data["references"]["Post"][item]
                        if "title" in item_data and "uniqueSlug" in item_data:
                            if "content" in item_data and "subtitle" in item_data["content"]:
                                title = item_data["title"] + " " + item_data["content"]["subtitle"]
                                link = url_prefix + item_data["uniqueSlug"]
                                result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
