#!/usr/bin/env python

import os
import sys
import re
import json
import getopt
import logging
import logging.config
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
from bin.feed_maker_util import IO


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


LINK_PREFIX = "https://webtoon.kakao.com/content"


def compose_description(item, link) -> str:
    description = "<div>\n"
    description += "    <div>%s</div>\n" % item["title"]
    description += "    <div>%s</div>\n" % ", ".join(item["seoKeywords"])
    description += "    <div>%s</div>\n" % item["catchphraseTwoLines"]
    description += "    <div><a href='%s'>%s</a></div>\n" % (link, link)
    description += "    <div><img src='%s'></div>\n" % (item["mergedImage"])
    description += "</div>\n"
    return description


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-f":
            _ = Path(a)
    return num_of_recent_feeds


def strip_outer_tags(content: str) -> str:
    """본문 앞뒤에 붙은 HTML 태그 묶음을 제거한다."""
    return re.sub(r"(^(<\S[^>]*>)+|(<\S[^>]*>)+$)", "", content)


def extract_items(
    json_data: dict, link_prefix: str = LINK_PREFIX
) -> List[Tuple[str, str]]:
    """data.sections → cardGroups → cards → content를 순회하며 날짜·성인여부를 반영한 (link, title) 목록을 만든다."""
    result_list: List[Tuple[str, str]] = []
    for section in json_data["data"]["sections"]:
        # section == weekday
        if "cardGroups" not in section:
            continue
        for card_group in section["cardGroups"]:
            if "cards" not in card_group:
                continue
            for card in card_group["cards"]:
                if "content" not in card:
                    continue

                item = card["content"]

                date_str = "1970-01-01"
                if "serialRestartDateTime" in item and item["serialRestartDateTime"]:
                    date_str = str(
                        datetime.fromisoformat(item["serialRestartDateTime"]).date()
                    )
                elif "serialStartDateTime" in item and item["serialStartDateTime"]:
                    date_str = str(
                        datetime.fromisoformat(item["serialStartDateTime"]).date()
                    )

                link = "%s/%s/%s" % (link_prefix, item["seoId"], item["id"])
                title = date_str + " " + item["title"]
                if "adult" in item and item["adult"]:
                    title += " (성인)"
                result_list.append((link, title))
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """제목 내림차순으로 정렬한 뒤 'link\\ttitle' 라인 목록으로 변환."""
    sorted_list = sorted(result_list, key=lambda obj: obj[1], reverse=True)
    return [
        "%s\t%s" % (link, title) for (link, title) in sorted_list[:num_of_recent_feeds]
    ]


def main() -> int:
    num_of_recent_feeds = parse_args(sys.argv[1:])

    content = strip_outer_tags(IO.read_stdin())
    json_data = json.loads(content)
    if "data" not in json_data:
        return -1
    if "sections" not in json_data["data"]:
        return -1

    result_list = extract_items(json_data)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)

    return 0


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

            # --- compose_description ---

            def test_compose_description_contains_fields(self):
                item = {
                    "title": "My Toon",
                    "seoKeywords": ["a", "b"],
                    "catchphraseTwoLines": "catchy",
                    "mergedImage": "http://img.test/x.png",
                }
                out = compose_description(item, "http://l.test/1")
                self.assertIn("<div>My Toon</div>", out)
                self.assertIn("<div>a, b</div>", out)
                self.assertIn("<div>catchy</div>", out)
                self.assertIn("<a href='http://l.test/1'>http://l.test/1</a>", out)
                self.assertIn("<img src='http://img.test/x.png'>", out)

            # --- strip_outer_tags ---

            def test_strip_outer_tags(self):
                self.assertEqual(strip_outer_tags("<pre>{}</pre>"), "{}")

            # --- extract_items ---

            def _json(self, contents):
                return {
                    "data": {
                        "sections": [
                            {
                                "cardGroups": [
                                    {"cards": [{"content": c} for c in contents]}
                                ]
                            }
                        ]
                    }
                }

            def test_extract_items_uses_restart_date(self):
                data = self._json(
                    [
                        {
                            "seoId": "s",
                            "id": "1",
                            "title": "T",
                            "serialRestartDateTime": "2024-05-01T00:00:00",
                            "serialStartDateTime": "2020-01-01T00:00:00",
                        }
                    ]
                )
                self.assertEqual(
                    extract_items(data),
                    [("https://webtoon.kakao.com/content/s/1", "2024-05-01 T")],
                )

            def test_extract_items_falls_back_to_start_date(self):
                data = self._json(
                    [
                        {
                            "seoId": "s",
                            "id": "1",
                            "title": "T",
                            "serialStartDateTime": "2020-01-02T00:00:00",
                        }
                    ]
                )
                self.assertEqual(extract_items(data)[0][1], "2020-01-02 T")

            def test_extract_items_default_date(self):
                data = self._json([{"seoId": "s", "id": "1", "title": "T"}])
                self.assertEqual(extract_items(data)[0][1], "1970-01-01 T")

            def test_extract_items_adult_suffix(self):
                data = self._json(
                    [{"seoId": "s", "id": "1", "title": "T", "adult": True}]
                )
                self.assertTrue(extract_items(data)[0][1].endswith(" (성인)"))

            def test_extract_items_skips_section_without_card_groups(self):
                data = {"data": {"sections": [{"foo": 1}]}}
                self.assertEqual(extract_items(data), [])

            # --- render_lines ---

            def test_render_lines_sorts_desc_by_title(self):
                result = [("l1", "2020-01-01 A"), ("l2", "2024-01-01 B")]
                self.assertEqual(
                    render_lines(result, 1000),
                    ["l2\t2024-01-01 B", "l1\t2020-01-01 A"],
                )

            def test_render_lines_limit(self):
                result = [("l1", "C"), ("l2", "B"), ("l3", "A")]
                self.assertEqual(render_lines(result, 2), ["l1\tC", "l2\tB"])

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
