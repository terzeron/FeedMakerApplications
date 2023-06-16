#!/usr/bin/env python


import sys
import os
import re
import getopt
from pathlib import Path
import logging.config
from feed_maker_util import Config, IO, URL


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
LOGGER = logging.getLogger(__name__)


def get_url_from_config(feed_dir_path: Path):
    config = Config(feed_dir_path=feed_dir_path)
    collection = config.get_collection_configs()
    url = collection["list_url_list"][0]
    return url


def main():
    feed_dir_path = Path.cwd()
    num_of_recent_feeds = 1000

    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-f':
            feed_dir_path = Path(a)
        elif o == '-n':
            num_of_recent_feeds = int(a)

    url = get_url_from_config(feed_dir_path)
    url = URL.get_url_scheme(url) + "://" + URL.get_url_domain(url) + "/"

    line_list = IO.read_stdin_as_line_list()
    result_list = []
    state = 0
    for line in line_list:
        if state == 0:
            m = re.search(r'<strong class="title">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="/(?P<article_id>\d+)"[^>]*title="(?P<title>[^"]+)"[^>]*>', line)
            if m:
                link = url + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))
                state = 2
        elif state == 2:
            m = re.search(r'</strong>', line)
            if m:
                state = 0

    for line in line_list:
        m = re.search(r'<a href="/(?P<link>\d+)"[^>]*title="(?P<title>[^"]+)"', line)
        if m:
            link = url + m.group("link")
            title = m.group("title")
            result_list.append((link, title))

    for (link, title) in result_list[-num_of_recent_feeds:]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
