#!/usr/bin/env python


import sys
import re
import json
import getopt
from typing import List, Tuple
from feed_maker_util import IO, URL


def main() -> int:
    link = ""
    title = ""

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
    url = args[0]

    content = IO.read_stdin()
    result_list: List[Tuple[str, str]] = []
    content = re.sub(r';$', '', re.sub(r'^var\s+clist\s*=\s*', '', content))
    data = json.loads(content)
    for item in data:
        link = URL.concatenate_url(url, item["u"])
        title = item["t"]
        result_list.append((link, title))
        
    num = len(result_list)
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%03d. %s" % (link, num, title))
        num = num - 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
