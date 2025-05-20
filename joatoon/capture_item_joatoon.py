#!/usr/bin/env python


import sys
import getopt
import re
from pathlib import Path
from bin.feed_maker_util import IO, Config, URL


class InsufficientConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)


def get_url_prefix_from_config(feed_dir_path: Path):
    config = Config(feed_dir_path)
    conf = config.get_collection_configs()
    url_list = conf.get("list_url_list", [])
    if url_list:
        url = url_list[0]
        return URL.get_url_scheme(url) + "://" + URL.get_url_domain(url) + "/webtoon"
    raise InsufficientConfigError("Can't get url prefix from configuration")


def main():
    link = ""
    title = ""
    feed_dir_path = Path.cwd()

    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-f":
            feed_dir_path = Path(a)

    state = 0
    result_list = []
    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(r'<div class="flex items-center">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)"', line)
            if m:
                link = m.group("link")
                state = 2
        elif state == 2:
            m = re.search(r'class="[^"]+"', line)
            if m:
                state = 3
        elif state == 3:
            m = re.search(r'^\s*(?P<title>\S.+\S)\s*$', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
