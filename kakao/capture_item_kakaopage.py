#!/usr/bin/env python


import os
import sys
import re
import json
import getopt
from pathlib import Path
import logging
import logging.config
from bin.feed_maker_util import IO, Config
from bin.crawler import Crawler, Method


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger(__name__)


def main() -> int:
    feed_dir_path = Path.cwd()
    num_of_recent_feeds = 20

    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        if o == "-n":
            num_of_recent_feeds = int(a)

    series_id = None
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'"seriesId"\s*:\s*(?P<series_id>\d+)', line)
        if m:
            series_id = m.group("series_id")
    if not series_id:
        LOGGER.error("can't find series id from HTML")
        return -1

    api_url = "https://api2-page.kakao.com/api/v5/store/singles"
    data = {"seriesid": series_id, "page": 0, "direction": "desc", "page_size": num_of_recent_feeds, "without_hidden": "true"}
    crawler = Crawler(dir_path=feed_dir_path, render_js=False, method=Method.POST)
    result, error, _ = crawler.run(api_url, data)
    if error:
        LOGGER.error(f"Error: can't get list data from '{api_url}'")
        return -1

    try:
        response = json.loads(result)
    except json.decoder.JSONDecodeError:
        LOGGER.error("Error: can't decode response to json")
        return -1

    url_prefix = "https://page.kakao.com/viewer?productId="
    result_list = []
    if "singles" in response:
        for s in response["singles"]:
            #pprint.pprint(s)
            link = url_prefix + str(s["id"])
            title = s["title"]
            result_list.append((link, title))

    for link, title in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
