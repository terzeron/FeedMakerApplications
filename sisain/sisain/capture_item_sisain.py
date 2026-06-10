#!/usr/bin/env python


import os
import sys
import json
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "https://sisain.co.kr/news/articleView.html?idxno="


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(argv, "n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def extract_items(
    json_data: dict, url_prefix: str = URL_PREFIX
) -> List[Tuple[str, str]]:
    """JSON data 배열에서 (link, title) 목록을 추출."""
    result_list: List[Tuple[str, str]] = []
    if json_data and "data" in json_data:
        for item in json_data["data"]:
            title = item["title"]
            link = url_prefix + item["idxno"]
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

        class TestCaptureItemSisain(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 30)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- extract_items ---

            def test_extract_items_basic(self):
                data = {"data": [{"title": "News 1", "idxno": "100"}]}
                self.assertEqual(
                    extract_items(data),
                    [
                        (
                            "https://sisain.co.kr/news/articleView.html?idxno=100",
                            "News 1",
                        )
                    ],
                )

            def test_extract_items_multiple(self):
                data = {
                    "data": [
                        {"title": "A", "idxno": "1"},
                        {"title": "B", "idxno": "2"},
                    ]
                }
                self.assertEqual([t for _, t in extract_items(data)], ["A", "B"])

            def test_extract_items_no_data(self):
                self.assertEqual(extract_items({}), [])

            def test_extract_items_none(self):
                self.assertEqual(extract_items(None), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 30), ["l1\tA", "l2\tB"]
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
