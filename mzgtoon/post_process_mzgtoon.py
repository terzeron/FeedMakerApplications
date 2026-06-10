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
    m = re.search(r"(?P<number>\d+)\.", file)
    return int(m.group("number")) if m else 0


def sort_numbered_files(file_list: List[str]) -> List[str]:
    return sorted(file_list, key=extract_number)


def parse_page_url(page_url: str):
    """페이지 URL에서 (url_prefix, webtoon_id, episode_id)를 추출(형식이 안 맞으면 None)."""
    m = re.search(
        r"^(?P<url_prefix>http.+)/webtoon/(?P<webtoon_id>\d+)/(?P<episode_id>\d+(\.\d+)?)$",
        page_url,
    )
    if not m:
        return None
    return m.group("url_prefix"), m.group("webtoon_id"), m.group("episode_id")


def build_image_links(
    img_list: List[str], url_prefix: str, webtoon_id: str, episode_id: str
) -> List[str]:
    """이미지 파일 목록을 번호순으로 정렬해 절대 URL 목록으로 변환."""
    return [
        f"{url_prefix}/webtoondata/{webtoon_id}/img/{episode_id}/{img}"
        for img in sort_numbered_files(img_list)
    ]


def main() -> int:
    feed_dir_path = Path.cwd()
    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)

    IO.read_stdin()

    page_url = args[0]
    parsed = parse_page_url(page_url)
    if not parsed:
        LOGGER.error("can't get URL information from command-line argument")
        return -1
    url_prefix, webtoon_id, episode_id = parsed
    api_url = f"{url_prefix}/api/getViewData?webtoonID={webtoon_id}&episodeID={episode_id}&sort=asc"

    print(header_str)

    crawler = Crawler(dir_path=feed_dir_path)
    result, error, _ = crawler.run(api_url)
    if not result or error:
        LOGGER.error("can't get image list from API '%s'", api_url)
        return -1

    data = json.loads(result)
    img_list = data.get("view_image", [])
    for link in build_image_links(img_list, url_prefix, webtoon_id, episode_id):
        print(f"<img src='{link}' />")

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessMzgtoon(unittest.TestCase):
            # --- extract_number ---

            def test_extract_number_basic(self):
                self.assertEqual(extract_number("012.jpg"), 12)

            def test_extract_number_no_number(self):
                self.assertEqual(extract_number("cover.png"), 0)

            # --- sort_numbered_files ---

            def test_sort_numbered_files_orders_by_number(self):
                self.assertEqual(
                    sort_numbered_files(["10.jpg", "2.jpg", "1.jpg"]),
                    ["1.jpg", "2.jpg", "10.jpg"],
                )

            def test_sort_numbered_files_empty(self):
                self.assertEqual(sort_numbered_files([]), [])

            # --- parse_page_url ---

            def test_parse_page_url_basic(self):
                self.assertEqual(
                    parse_page_url("https://m.test/webtoon/100/5"),
                    ("https://m.test", "100", "5"),
                )

            def test_parse_page_url_decimal_episode(self):
                self.assertEqual(
                    parse_page_url("https://m.test/webtoon/100/5.1"),
                    ("https://m.test", "100", "5.1"),
                )

            def test_parse_page_url_invalid(self):
                self.assertIsNone(parse_page_url("https://m.test/other/1"))

            # --- build_image_links ---

            def test_build_image_links_sorted(self):
                self.assertEqual(
                    build_image_links(["2.jpg", "1.jpg"], "https://m.test", "100", "5"),
                    [
                        "https://m.test/webtoondata/100/img/5/1.jpg",
                        "https://m.test/webtoondata/100/img/5/2.jpg",
                    ],
                )

            def test_build_image_links_empty(self):
                self.assertEqual(build_image_links([], "p", "1", "1"), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
