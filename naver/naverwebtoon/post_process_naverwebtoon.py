#!/usr/bin/env python


import sys
import os
import re
import json
import getopt
import logging
import logging.config
from typing import List
from pathlib import Path
from bin.feed_maker_util import IO, Process, Config, URL, header_str
from bin.crawler import Crawler


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def main() -> int:
    feed_dir_path = Path.cwd()
    url_prefix = "https://comic.naver.com/api/article/list/info?titleId="
    exclude_keywords = ["로맨스", "연인", "연애", "키스", "짝사랑", "고백", "유부녀", "황후", "왕후", "왕비", "공녀", "첫사랑", "재벌", "순정", "후궁", "로판", "로맨스판타지", "멜로"]

    IO.read_stdin()

    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        if o == "-n":
            num_of_recent_feeds = int(a)

    print(header_str)

    page_url = args[0]
    m = re.search(r'titleId=(?P<title_id>\d+)', page_url)
    if m:
        title_id = m.group("title_id")
        link = url_prefix + title_id
        crawler = Crawler(dir_path=feed_dir_path)
        result, error, _ = crawler.run(link)
        if error:
            LOGGER.error(f"Error: can't get data from '{link}'")
            return -1

        json_data = json.loads(result)
        if "titleName" in json_data:
            print("<p>" + json_data["titleName"] + "</p>")
        if "synopsis" in json_data:
            print("<p>" + json_data["synopsis"] + "</p>")
        if "thumbnailUrl" in json_data:
            print("<p><img src='" + json_data["thumbnailUrl"] + "'></p>")

    config = Config(feed_dir_path)
    if not config:
        LOGGER.error("can't read configuration")
        return -1
    rss_conf = config.get_rss_configs()
    m = re.search(r'https://[^/]+/(?P<rss_file_name>.+\.xml)', rss_conf["rss_link"])
    if m:
        rss_file_name = m.group("rss_file_name")
        md5_name = URL.get_short_md5_name(URL.get_url_path(page_url))
        print("<img src='https://terzeron.com/img/1x1.jpg?feed=%s&item=%s'/>" % (rss_file_name, md5_name))

    return 0


if __name__ == "__main__":
    sys.exit(main())
