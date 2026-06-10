#!/usr/bin/env python


import os
import sys
import json
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "https://brunch.co.kr/@"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def extract_items(json_data: dict) -> List[Tuple[str, str]]:
    """brunch JSON(data.list)에서 (link, title) 목록을 추출."""
    result_list: List[Tuple[str, str]] = []
    if json_data and "data" in json_data and "list" in json_data["data"]:
        for item in json_data["data"]["list"]:
            link = (
                URL_PREFIX
                + item["user"]["profileId"]
                + "/"
                + str(item["article"]["no"])
            )
            title = item["article"]["title"]
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

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "3"]), 3)

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "."]), 1000)

            # --- extract_items ---

            def _data(self, items):
                return {
                    "data": {
                        "list": [
                            {
                                "user": {"profileId": pid},
                                "article": {"no": no, "title": title},
                            }
                            for pid, no, title in items
                        ]
                    }
                }

            def test_extract_items_basic(self):
                data = self._data([("alice", 12, "Hello")])
                self.assertEqual(
                    extract_items(data),
                    [("https://brunch.co.kr/@alice/12", "Hello")],
                )

            def test_extract_items_multiple(self):
                data = self._data([("a", 1, "T1"), ("b", 2, "T2")])
                self.assertEqual(
                    extract_items(data),
                    [
                        ("https://brunch.co.kr/@a/1", "T1"),
                        ("https://brunch.co.kr/@b/2", "T2"),
                    ],
                )

            def test_extract_items_no_data_key(self):
                self.assertEqual(extract_items({}), [])

            def test_extract_items_no_list_key(self):
                self.assertEqual(extract_items({"data": {}}), [])

            def test_extract_items_empty_list(self):
                self.assertEqual(extract_items({"data": {"list": []}}), [])

            def test_extract_items_none(self):
                self.assertEqual(extract_items(None), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 1000),
                    ["l1\tA", "l2\tB"],
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 list_url(https://api.brunch.co.kr/v1/magazine/37474/articles)을
            #       받아온 실제 JSON 중 파서가 읽는 필드(data.list[].user.profileId,
            #       article.no, article.title)만 item 3개로 샘플링한 것.
            # 기대 출력: 동일 입력을 'capture_item_link_title.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_DATA = {
                "data": {
                    "list": [
                        {
                            "user": {"profileId": "hvnpoet"},
                            "article": {
                                "no": 189,
                                "title": "AI의 흐름을 만드는 CEO, 해리슨 체이스",
                            },
                        },
                        {
                            "user": {"profileId": "hvnpoet"},
                            "article": {
                                "no": 190,
                                "title": "AI 혁명의 삼각편대, 클레망 들랑그 외",
                            },
                        },
                        {
                            "user": {"profileId": "hvnpoet"},
                            "article": {
                                "no": 188,
                                "title": "파운드리 혁명가, 모리스 창",
                            },
                        },
                    ]
                }
            }

            def test_real_sample_end_to_end(self):
                result = extract_items(self.REAL_SAMPLE_DATA)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://brunch.co.kr/@hvnpoet/189\tAI의 흐름을 만드는 CEO, 해리슨 체이스",
                        "https://brunch.co.kr/@hvnpoet/190\tAI 혁명의 삼각편대, 클레망 들랑그 외",
                        "https://brunch.co.kr/@hvnpoet/188\t파운드리 혁명가, 모리스 창",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
