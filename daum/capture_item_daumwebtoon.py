#!/usr/bin/env python

import os
import sys
import json
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


LINK_PREFIX = "http://cartoon.media.daum.net/m/webtoon/viewer/"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def extract_items(
    json_data: dict, link_prefix: str = LINK_PREFIX
) -> List[Tuple[str, str]]:
    """data.webtoon.webtoonEpisodes에서 유료(price>0) 회차를 제외하고 (link, title) 목록을 추출."""
    link = ""
    title = ""
    result_list: List[Tuple[str, str]] = []
    if (
        "data" in json_data
        and "webtoon" in json_data["data"]
        and "webtoonEpisodes" in json_data["data"]["webtoon"]
    ):
        for episode in json_data["data"]["webtoon"]["webtoonEpisodes"]:
            if "price" in episode and episode["price"] > 0:
                continue
            if "title" in episode:
                title = episode["title"]
            if "articleId" in episode:
                link = link_prefix + str(episode["articleId"])
            if title and link:
                result_list.append((link, title))
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """(link, title) 목록을 'link\\ttitle' 라인 목록으로 변환."""
    return [
        "%s\t%s" % (link, title) for (link, title) in result_list[:num_of_recent_feeds]
    ]


def main():
    num_of_recent_feeds = parse_args(sys.argv[1:])

    content = IO.read_stdin()
    json_data = json.loads(content)
    result_list = extract_items(json_data)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemDaumwebtoon(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "4"]), 4)

            # --- extract_items ---

            def _data(self, episodes):
                return {"data": {"webtoon": {"webtoonEpisodes": episodes}}}

            def test_extract_items_basic(self):
                data = self._data([{"articleId": 10, "title": "1화"}])
                self.assertEqual(
                    extract_items(data),
                    [("http://cartoon.media.daum.net/m/webtoon/viewer/10", "1화")],
                )

            def test_extract_items_skips_paid(self):
                data = self._data(
                    [
                        {"articleId": 1, "title": "free", "price": 0},
                        {"articleId": 2, "title": "paid", "price": 100},
                    ]
                )
                self.assertEqual([t for _, t in extract_items(data)], ["free"])

            def test_extract_items_no_data_key(self):
                self.assertEqual(extract_items({}), [])

            def test_extract_items_no_webtoon_key(self):
                self.assertEqual(extract_items({"data": {}}), [])

            def test_extract_items_empty_episodes(self):
                self.assertEqual(extract_items(self._data([])), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 1000), ["l1\tA", "l2\tB"]
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
