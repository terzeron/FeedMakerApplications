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
from bin.feed_maker_util import IO, Config, URL, header_str
from bin.crawler import Crawler


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def print_img_tag(feed_dir_path: Path, page_url: str) -> None:
    config = Config(feed_dir_path)
    if not config:
        LOGGER.error("can't read configuration")
        return
    rss_conf = config.get_rss_configs()
    m = re.search(r'https://[^/]+/(?P<rss_file_name>.+\.xml)', rss_conf["rss_link"])
    if m:
        rss_file_name = m.group("rss_file_name")
        md5_name = URL.get_short_md5_name(URL.get_url_path(page_url))
        print(f"<img src='https://terzeron.com/img/1x1.jpg?feed={rss_file_name}&item={md5_name}'/>")


def main() -> int:
    feed_dir_path = Path.cwd()
    url_prefix = "https://comic.naver.com/api/article/list/info?titleId="

    IO.read_stdin()

    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        if o == "-n":
            _ = int(a)

    tag_list: List = []
    page_url = args[0]
    m = re.search(r'titleId=(?P<title_id>\d+)', page_url)
    if m:
        title_id = m.group("title_id")
        link = url_prefix + title_id
        crawler = Crawler(dir_path=feed_dir_path)
        result, error, _ = crawler.run(link)
        del crawler
        if error:
            LOGGER.error("Error: can't get data from '%s'", link)
            return -1

        json_data = json.loads(result)

        if "curationTagList" in json_data:
            for curation in json_data["curationTagList"]:
                if "tagName" in curation:
                    tag_list.append(curation["tagName"])

        if "titleName" in json_data:
            title_name = json_data["titleName"]
        if "synopsis" in json_data:
            synopsis = json_data["synopsis"]
        if "thumbnailUrl" in json_data:
            thumbnail_url = json_data["thumbnailUrl"]

        print(header_str)
        print("<p>" + title_name + "</p>")
        print("<p>" + synopsis + "</p>")
        print("<p><img src='" + thumbnail_url + "'></p>")
        print("<ul>")
        for tag in tag_list:
            print("<li>#" + tag + "</li>")
        print("</ul>")
        print_img_tag(feed_dir_path, page_url)

    return 0


if __name__ == "__main__":
    sys.exit(main())
