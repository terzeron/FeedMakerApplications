#!/usr/bin/env python

import os
import sys
import re
import json
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


LINK_PREFIX = "https://page.kakao.com/content"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def strip_outer_tags(content: str) -> str:
    """본문 앞뒤에 붙은 HTML 태그 묶음을 제거한다."""
    return re.sub(r"(^(<\S[^>]*>)+|(<\S[^>]*>)+$)", "", content)


def extract_items(
    json_data: dict, link_prefix: str = LINK_PREFIX
) -> List[Tuple[str, str]]:
    """product/list 응답에서 성인용이 아니고 무료(is_free)인 회차만 (link, title)로 추출.

    응답 순서(sort_type=desc, 최신순)를 그대로 유지한다.
    """
    result_list: List[Tuple[str, str]] = []
    result = json_data.get("result", {})
    series_id = result.get("series_item", {}).get("id")
    if not series_id:
        return result_list
    for entry in result.get("list", []):
        item = entry.get("item", {})
        if (
            item.get("age_grade", 0) != 0
            or item.get("hidden")
            or not item.get("is_free")
        ):
            continue
        link = "%s/%s/viewer/%s" % (link_prefix, series_id, item["product_id"])
        # 정렬 키(sort_field_pattern)는 회차 번호이므로 order_value를 쓰고, 없으면 제목에서 뽑는다.
        no = item.get("order_value")
        if no is None:
            m = re.search(r"(\d+)", item.get("title", ""))
            if not m:
                continue
            no = m.group(1)
        title = "%s. %s" % (no, item["title"])
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

    content = strip_outer_tags(IO.read_stdin())
    json_data = json.loads(content)
    result_list = extract_items(json_data)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCapture(unittest.TestCase):
            def _data(self, entries, series_id=60105861):
                return {"result": {"series_item": {"id": series_id}, "list": entries}}

            def _entry(self, pid, title, no=None, free=True, age=0, hidden=False):
                item = {
                    "product_id": pid,
                    "title": title,
                    "is_free": free,
                    "age_grade": age,
                    "hidden": hidden,
                }
                if no is not None:
                    item["order_value"] = no
                return {"item": item}

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "7"]), 7)

            def test_strip_outer_tags(self):
                self.assertEqual(strip_outer_tags("<pre>{}</pre>"), "{}")

            def test_extract_basic(self):
                data = self._data([self._entry(70352693, "264화", 264)])
                self.assertEqual(
                    extract_items(data),
                    [
                        (
                            "https://page.kakao.com/content/60105861/viewer/70352693",
                            "264. 264화",
                        )
                    ],
                )

            def test_extract_skips_paid_adult_hidden(self):
                data = self._data(
                    [
                        self._entry(1, "a", 3, free=False),
                        self._entry(2, "b", 2, age=19),
                        self._entry(3, "c", 1, hidden=True),
                    ]
                )
                self.assertEqual(extract_items(data), [])

            def test_extract_title_fallback_for_no(self):
                data = self._data([self._entry(5, "12화")])
                self.assertEqual(extract_items(data)[0][1], "12. 12화")

            def test_extract_keeps_order(self):
                data = self._data([self._entry(2, "2화", 2), self._entry(1, "1화", 1)])
                self.assertEqual(
                    [t for _, t in extract_items(data)], ["2. 2화", "1. 1화"]
                )

            def test_extract_no_series_or_empty(self):
                self.assertEqual(extract_items({}), [])
                self.assertEqual(extract_items({"result": {"list": []}}), [])

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
