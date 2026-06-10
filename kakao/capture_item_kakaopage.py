#!/usr/bin/env python


import os
import sys
import re
import json
import getopt
from pathlib import Path
from typing import List, Optional, Tuple
import logging
import logging.config
from bin.feed_maker_util import IO
from bin.crawler import Crawler, Method


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger(__name__)


URL_PREFIX = "https://page.kakao.com/viewer?productId="


def parse_args(argv: List[str]) -> Tuple[Path, int]:
    """명령행 인자를 파싱해 (feed_dir_path, num_of_recent_feeds)를 반환."""
    feed_dir_path = Path.cwd()
    num_of_recent_feeds = 20
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        if o == "-n":
            num_of_recent_feeds = int(a)
    return feed_dir_path, num_of_recent_feeds


def find_series_id(line_list: List[str]) -> Optional[str]:
    """HTML 라인에서 마지막으로 발견되는 seriesId를 반환(없으면 None)."""
    series_id = None
    for line in line_list:
        m = re.search(r'"seriesId"\s*:\s*(?P<series_id>\d+)', line)
        if m:
            series_id = m.group("series_id")
    return series_id


def extract_items(
    response: dict, url_prefix: str = URL_PREFIX
) -> List[Tuple[str, str]]:
    """API 응답(response.singles)에서 (link, title) 목록을 추출."""
    result_list: List[Tuple[str, str]] = []
    if "singles" in response:
        for s in response["singles"]:
            link = url_prefix + str(s["id"])
            title = s["title"]
            result_list.append((link, title))
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """(link, title) 목록을 'link\\ttitle' 라인 목록으로 변환."""
    return [
        "%s\t%s" % (link, title) for (link, title) in result_list[:num_of_recent_feeds]
    ]


def main() -> int:
    feed_dir_path, num_of_recent_feeds = parse_args(sys.argv[1:])

    series_id = find_series_id(IO.read_stdin_as_line_list())
    if not series_id:
        LOGGER.error("can't find series id from HTML")
        return -1

    api_url = "https://api2-page.kakao.com/api/v5/store/singles"
    data = {
        "seriesid": series_id,
        "page": 0,
        "direction": "desc",
        "page_size": num_of_recent_feeds,
        "without_hidden": "true",
    }
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

    result_list = extract_items(response)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemKakaopage(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default_num(self):
                self.assertEqual(parse_args([])[1], 20)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"])[1], 5)

            def test_parse_args_feed_dir(self):
                self.assertEqual(parse_args(["-f", "/tmp/x"])[0], Path("/tmp/x"))

            # --- find_series_id ---

            def test_find_series_id_basic(self):
                self.assertEqual(
                    find_series_id(["x", '"seriesId": 12345', "y"]), "12345"
                )

            def test_find_series_id_last_wins(self):
                self.assertEqual(
                    find_series_id(['"seriesId": 1', '"seriesId": 2']), "2"
                )

            def test_find_series_id_none(self):
                self.assertIsNone(find_series_id(["no id here"]))

            # --- extract_items ---

            def test_extract_items_basic(self):
                response = {"singles": [{"id": 100, "title": "1화"}]}
                self.assertEqual(
                    extract_items(response),
                    [("https://page.kakao.com/viewer?productId=100", "1화")],
                )

            def test_extract_items_multiple(self):
                response = {
                    "singles": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]
                }
                self.assertEqual([t for _, t in extract_items(response)], ["A", "B"])

            def test_extract_items_no_singles(self):
                self.assertEqual(extract_items({}), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 20), ["l1\tA", "l2\tB"]
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 20), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
