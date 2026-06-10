#!/usr/bin/env python


import os
import sys
import json
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "https://comic.naver.com/webtoon/list?titleId="


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def extract_items(
    json_data: dict, url_prefix: str = URL_PREFIX
) -> List[Tuple[str, str]]:
    """titleList에서 (link, title) 목록을 추출(성인물은 제목에 (성인) 표시)."""
    link = ""
    result_list: List[Tuple[str, str]] = []
    if "titleList" in json_data:
        for data_item in json_data["titleList"]:
            if "titleId" in data_item:
                title_id = data_item["titleId"]
                link = url_prefix + str(title_id)
            if "titleName" in data_item:
                title = data_item["titleName"]
                if "adult" in data_item and data_item["adult"]:
                    title += " (성인)"
                result_list.append((link, title))
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """titleId 내림차순으로 정렬한 뒤 'link\\ttitle' 라인 목록으로 변환."""
    sorted_list = sorted(
        result_list, key=lambda obj: int(obj[0].split("=")[1]), reverse=True
    )
    return [f"{link}\t{title}" for (link, title) in sorted_list[:num_of_recent_feeds]]


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

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- extract_items ---

            def test_extract_items_basic(self):
                data = {"titleList": [{"titleId": 100, "titleName": "Toon"}]}
                self.assertEqual(
                    extract_items(data),
                    [("https://comic.naver.com/webtoon/list?titleId=100", "Toon")],
                )

            def test_extract_items_adult_suffix(self):
                data = {"titleList": [{"titleId": 1, "titleName": "X", "adult": True}]}
                self.assertTrue(extract_items(data)[0][1].endswith(" (성인)"))

            def test_extract_items_multiple(self):
                data = {
                    "titleList": [
                        {"titleId": 1, "titleName": "A"},
                        {"titleId": 2, "titleName": "B"},
                    ]
                }
                self.assertEqual([t for _, t in extract_items(data)], ["A", "B"])

            def test_extract_items_no_title_list(self):
                self.assertEqual(extract_items({}), [])

            # --- render_lines ---

            def test_render_lines_sorts_by_title_id_desc(self):
                result = [
                    ("https://c/list?titleId=1", "A"),
                    ("https://c/list?titleId=20", "B"),
                    ("https://c/list?titleId=3", "C"),
                ]
                self.assertEqual(
                    [
                        t
                        for line in render_lines(result, 1000)
                        for t in [line.split("\t")[1]]
                    ],
                    ["B", "C", "A"],
                )

            def test_render_lines_limit(self):
                result = [
                    ("https://c/list?titleId=1", "A"),
                    ("https://c/list?titleId=2", "B"),
                    ("https://c/list?titleId=3", "C"),
                ]
                self.assertEqual(len(render_lines(result, 2)), 2)

        sys.exit(unittest.main())
    else:
        sys.exit(main())
