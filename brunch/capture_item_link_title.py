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

        sys.exit(unittest.main())
    else:
        sys.exit(main())
