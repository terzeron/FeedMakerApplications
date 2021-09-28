#!/usr/bin/env python


import sys
import re
import json
import getopt
from typing import List, Tuple
from feed_maker_util import IO, URL, Config


def get_url_from_config():
    config = Config()
    collection = config.get_collection_configs()
    url = collection["list_url_list"][0]
    return url


def main() -> int:
    link = ""
    title = ""
    site_url = get_url_from_config()

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for chunk in line_list:
        for line in chunk.split("</p>"):
            m = re.search(r'<a href="(?P<link>[^"]+)"[^>]*>\s*<div [^>]*>\s*<p [^>]*>(?P<title>[^<]+)', line)
            if m:
                link = URL.concatenate_url(site_url, m.group("link"))
                title = m.group("title")
                result_list.append((link, title))
        
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
