#!/usr/bin/env python


import os
import sys
import re
import getopt
import json
from typing import List, Tuple
from bin.feed_maker_util import IO


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def extract_posts(json_data: dict, page_url: str) -> List[Tuple[str, str]]:
    """obvInit JSON의 references.Post에서 (link, title) 목록을 추출."""
    result_list: List[Tuple[str, str]] = []
    if json_data and "references" in json_data and "Post" in json_data["references"]:
        for item in json_data["references"]["Post"]:
            item_data = json_data["references"]["Post"][item]
            if "title" in item_data and "uniqueSlug" in item_data:
                if "content" in item_data and "subtitle" in item_data["content"]:
                    main_title = re.sub(r"\n", " ", item_data["title"])
                    sub_title = re.sub(r"\n", " ", item_data["content"]["subtitle"])
                    title = main_title + " " + sub_title
                    link = page_url + "/" + item_data["uniqueSlug"]
                    result_list.append((link, title))
    return result_list


def parse_feed_list(line_list: List[str]) -> List[Tuple[str, str]]:
    """canonical URL을 잡은 뒤 window["obvInit"] JSON에서 (link, title) 목록을 만든다."""
    page_url = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<link rel="canonical" href="(?P<page_url>[^"]+)">', line)
            if m:
                page_url = m.group("page_url")
                state = 1
        elif state == 1:
            m = re.search(r'^window\["obvInit"\]\((?P<json>.*)\)$', line)
            if m:
                json_content = m.group("json")
                json_content = json_content.replace(r"\x3c", "<")
                json_content = json_content.replace(r"\x3e", ">")
                json_data = json.loads(json_content)
                result_list.extend(extract_posts(json_data, page_url))
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

    line_list = IO.read_stdin_as_line_list()
    result_list = parse_feed_list(line_list)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemMedium(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "4"]), 4)

            # --- extract_posts ---

            def _data(self, posts):
                return {"references": {"Post": posts}}

            def test_extract_posts_basic(self):
                data = self._data(
                    {
                        "p1": {
                            "title": "Hello",
                            "uniqueSlug": "hello-abc",
                            "content": {"subtitle": "world"},
                        }
                    }
                )
                self.assertEqual(
                    extract_posts(data, "https://m.test/@u"),
                    [("https://m.test/@u/hello-abc", "Hello world")],
                )

            def test_extract_posts_collapses_newlines(self):
                data = self._data(
                    {
                        "p1": {
                            "title": "a\nb",
                            "uniqueSlug": "s",
                            "content": {"subtitle": "c\nd"},
                        }
                    }
                )
                self.assertEqual(extract_posts(data, "P")[0][1], "a b c d")

            def test_extract_posts_skips_without_subtitle(self):
                data = self._data(
                    {"p1": {"title": "T", "uniqueSlug": "s", "content": {}}}
                )
                self.assertEqual(extract_posts(data, "P"), [])

            def test_extract_posts_skips_without_slug(self):
                data = self._data({"p1": {"title": "T", "content": {"subtitle": "x"}}})
                self.assertEqual(extract_posts(data, "P"), [])

            def test_extract_posts_no_references(self):
                self.assertEqual(extract_posts({}, "P"), [])

            def test_extract_posts_none(self):
                self.assertEqual(extract_posts(None, "P"), [])

            # --- parse_feed_list ---

            def test_parse_feed_list_basic(self):
                obv = json.dumps(
                    {
                        "references": {
                            "Post": {
                                "p1": {
                                    "title": "T",
                                    "uniqueSlug": "s",
                                    "content": {"subtitle": "sub"},
                                }
                            }
                        }
                    }
                )
                lines = [
                    '<link rel="canonical" href="https://m.test/@u">',
                    f'window["obvInit"]({obv})',
                ]
                self.assertEqual(
                    parse_feed_list(lines), [("https://m.test/@u/s", "T sub")]
                )

            def test_parse_feed_list_requires_canonical(self):
                obv = json.dumps({"references": {"Post": {}}})
                self.assertEqual(parse_feed_list([f'window["obvInit"]({obv})']), [])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), [])

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

        sys.exit(unittest.main())
    else:
        sys.exit(main())
