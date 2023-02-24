#!/usr/bin/env python


import sys
import re
import json
import getopt
from pathlib import Path
from typing import List, Tuple
from feed_maker_util import IO, URL, Config


def get_url_from_config(feed_dir_path: Path):
    config = Config(feed_dir_path=feed_dir_path)
    collection = config.get_collection_configs()
    url = collection["list_url_list"][0]
    return url


def main() -> int:
    feed_dir_path = Path.cwd()
    num_of_recent_feeds = 1000

    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        elif o == '-n':
            num_of_recent_feeds = int(a)

    if not feed_dir_path or not feed_dir_path.is_dir():
        LOGGER.error(f"can't find such a directory '{feed_dir_path}'")
        return -1

    url_prefix = ""
    link = ""
    title = ""
    state = 0

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<meta property="og:url" content="(?P<url_prefix>https?://[^/]+)', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div class="body">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'</ul>', line)
            if m:
                break
            
            m = re.search(r'<li [^>]*onclick="location.href=\'(?P<link>[^\']+)\'"[^>]*><p>(?P<title>[^<]+)', line)
            if m:
                link = url_prefix + m.group("link")
                title = m.group("title")
                title = re.sub(r'&nbsp;', '', title)
                result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
