#!/usr/bin/env python


import sys
import os
import re
import json
import getopt
import logging
import logging.config
from pathlib import Path
from typing import List
from bin.feed_maker_util import IO, header_str
from bin.crawler import Crawler


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def extract_number(file: str) -> int:
    m = re.search(r'(?P<number>\d+)\.', file)
    return int(m.group("number")) if m else 0


def sort_numbered_files(file_list: List[str]) -> List[str]:
    return sorted(file_list, key=extract_number)


def main() -> int:
    feed_dir_path = Path.cwd()
    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)

    IO.read_stdin()

    page_url = args[0]
    m = re.search(r'^(?P<url_prefix>http.+)/webtoon/(?P<webtoon_id>\d+)/(?P<episode_id>\d+(\.\d+)?)$', page_url)
    if m:
        url_prefix = m.group("url_prefix")
        webtoon_id = m.group("webtoon_id")
        episode_id = m.group("episode_id")
        api_url = f"{url_prefix}/api/getViewData?webtoonID={webtoon_id}&episodeID={episode_id}&sort=asc"
    else:
        LOGGER.error("can't get URL information from command-line argument")
        return -1

    print(header_str)
    
    crawler = Crawler(dir_path=feed_dir_path)
    result, error, _ = crawler.run(api_url)
    if not result or error:
        LOGGER.error("can't get image list from API '%s'", api_url)
        return -1

    data = json.loads(result)
    img_list = data.get("view_image", [])
    img_list = sort_numbered_files(img_list)
    if img_list:
        for img in img_list:
            link = f"{url_prefix}/webtoondata/{webtoon_id}/img/{episode_id}/{img}"
            print(f"<img src='{link}' />")
    
    return 0
    

if __name__ == "__main__":
    sys.exit(main())
