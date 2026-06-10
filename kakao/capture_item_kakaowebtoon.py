#!/usr/bin/env python

import os
import sys
import re
import json
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


LINK_PREFIX = "https://webtoon.kakao.com/viewer"


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
    """data.episodes에서 성인용이 아니고 무료(FREE)인 회차만 (link, title)로 추출."""
    result_list: List[Tuple[str, str]] = []
    if "data" in json_data and "episodes" in json_data["data"]:
        for episode in json_data["data"]["episodes"]:
            if not episode["adult"] and episode["useType"] == "FREE":
                link = "%s/%s/%s" % (link_prefix, episode["seoId"], episode["id"])
                title = "%s. %s" % (episode["no"], episode["title"])
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

        class TestCaptureItemKakaowebtoon(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "7"]), 7)

            # --- strip_outer_tags ---

            def test_strip_outer_tags_removes_leading_and_trailing(self):
                self.assertEqual(strip_outer_tags("<pre><code>{}</code></pre>"), "{}")

            def test_strip_outer_tags_plain_json_unchanged(self):
                self.assertEqual(strip_outer_tags('{"a":1}'), '{"a":1}')

            # --- extract_items ---

            def _ep(self, no, title, adult=False, use_type="FREE", seo="s", eid="1"):
                return {
                    "no": no,
                    "title": title,
                    "adult": adult,
                    "useType": use_type,
                    "seoId": seo,
                    "id": eid,
                }

            def test_extract_items_basic(self):
                data = {
                    "data": {"episodes": [self._ep(1, "Hello", seo="abc", eid="9")]}
                }
                self.assertEqual(
                    extract_items(data),
                    [("https://webtoon.kakao.com/viewer/abc/9", "1. Hello")],
                )

            def test_extract_items_skips_adult(self):
                data = {"data": {"episodes": [self._ep(1, "X", adult=True)]}}
                self.assertEqual(extract_items(data), [])

            def test_extract_items_skips_non_free(self):
                data = {"data": {"episodes": [self._ep(1, "X", use_type="PAY")]}}
                self.assertEqual(extract_items(data), [])

            def test_extract_items_no_episodes(self):
                self.assertEqual(extract_items({"data": {}}), [])

            def test_extract_items_no_data(self):
                self.assertEqual(extract_items({}), [])

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

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py(accept-language: ko + Chrome UA)로 gateway-kw.kakao.com episodes API에서
            #       받아온 실제 JSON 중 파서가 읽는 필드(data.episodes[].id/seoId/no/title/adult/useType)를
            #       무료(FREE) 회차 3개로 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_kakaowebtoon.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_DATA = {
                "data": {
                    "episodes": [
                        {
                            "id": 342537,
                            "seoId": "레드스톰---왕의-귀환-462",
                            "no": 462,
                            "title": "2부 70화",
                            "adult": False,
                            "useType": "FREE",
                        },
                        {
                            "id": 341855,
                            "seoId": "레드스톰---왕의-귀환-461",
                            "no": 461,
                            "title": "2부 69화",
                            "adult": False,
                            "useType": "FREE",
                        },
                        {
                            "id": 341208,
                            "seoId": "레드스톰---왕의-귀환-460",
                            "no": 460,
                            "title": "2부 68화",
                            "adult": False,
                            "useType": "FREE",
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
                        "https://webtoon.kakao.com/viewer/레드스톰---왕의-귀환-462/342537\t462. 2부 70화",
                        "https://webtoon.kakao.com/viewer/레드스톰---왕의-귀환-461/341855\t461. 2부 69화",
                        "https://webtoon.kakao.com/viewer/레드스톰---왕의-귀환-460/341208\t460. 2부 68화",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
