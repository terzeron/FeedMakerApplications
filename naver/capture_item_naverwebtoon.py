#!/usr/bin/env python


import os
import sys
import getopt
import json
from typing import List, Tuple

from bin.feed_maker_util import IO


URL_TEMPLATE = "https://comic.naver.com/webtoon/detail?titleId=%d&no=%d"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def extract_items(
    data: dict, url_template: str = URL_TEMPLATE
) -> List[Tuple[str, str]]:
    """titleId와 articleList에서 (link, title) 목록을 추출(no/subtitle 누락 시 직전 값 유지)."""
    link = ""
    title = ""
    result_list: List[Tuple[str, str]] = []
    if "titleId" in data and data["titleId"]:
        title_id = data["titleId"]
        if "articleList" in data and data["articleList"]:
            for article in data["articleList"]:
                if "no" in article and article["no"]:
                    no = article["no"]
                    link = url_template % (title_id, no)
                if "subtitle" in article and article["subtitle"]:
                    title = article["subtitle"]
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
    data = json.loads(content)
    result_list = extract_items(data)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemNaverWebtoon(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- extract_items ---

            def test_extract_items_basic(self):
                data = {"titleId": 100, "articleList": [{"no": 1, "subtitle": "Ep 1"}]}
                self.assertEqual(
                    extract_items(data),
                    [
                        (
                            "https://comic.naver.com/webtoon/detail?titleId=100&no=1",
                            "Ep 1",
                        )
                    ],
                )

            def test_extract_items_multiple(self):
                data = {
                    "titleId": 100,
                    "articleList": [
                        {"no": 1, "subtitle": "A"},
                        {"no": 2, "subtitle": "B"},
                    ],
                }
                self.assertEqual([t for _, t in extract_items(data)], ["A", "B"])

            def test_extract_items_keeps_previous_link_when_no_missing(self):
                # 'no'가 없는 항목은 직전 link를 유지한다
                data = {
                    "titleId": 100,
                    "articleList": [
                        {"no": 1, "subtitle": "A"},
                        {"subtitle": "B"},
                    ],
                }
                items = extract_items(data)
                self.assertEqual(items[0][0], items[1][0])

            def test_extract_items_no_title_id(self):
                self.assertEqual(extract_items({"articleList": [{"no": 1}]}), [])

            def test_extract_items_empty_article_list(self):
                self.assertEqual(extract_items({"titleId": 1, "articleList": []}), [])

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

        class TestNaverWebtoonSchema(unittest.TestCase):
            SAMPLE_INPUT_FOR_SCHEMA = """
{
  "titleId": 123456,
  "articleList": [
    { "no": 1, "subtitle": "Episode 1" },
    { "no": 2, "subtitle": "Episode 2" }
  ]
}
"""

            def _anonymize_recursive(self, obj):
                if isinstance(obj, dict):
                    return {k: self._anonymize_recursive(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [self._anonymize_recursive(obj[0])] if obj else []
                if isinstance(obj, str):
                    return "__STRING__"
                if isinstance(obj, int):
                    return "__NUMBER__"
                return obj

            def test_input_schema_is_unchanged(self):
                sample_data = json.loads(self.SAMPLE_INPUT_FOR_SCHEMA)
                golden_schema = self._anonymize_recursive(sample_data)
                self.assertEqual(self._anonymize_recursive(sample_data), golden_schema)

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://comic.naver.com/api/article/list?titleId=844731&sort=DESC 를
            #       받아온 실제 JSON 중 파서가 읽는 필드(titleId, articleList[].no/subtitle)만 3개로 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_naverwebtoon.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_DATA = {
                "titleId": 844731,
                "articleList": [
                    {"no": 28, "subtitle": "28화"},
                    {"no": 27, "subtitle": "27화"},
                    {"no": 26, "subtitle": "26화"},
                ],
            }

            def test_real_sample_end_to_end(self):
                result = extract_items(self.REAL_SAMPLE_DATA)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://comic.naver.com/webtoon/detail?titleId=844731&no=28\t28화",
                        "https://comic.naver.com/webtoon/detail?titleId=844731&no=27\t27화",
                        "https://comic.naver.com/webtoon/detail?titleId=844731&no=26\t26화",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
