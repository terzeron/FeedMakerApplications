#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "https://mmzone.co.kr"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def parse_feed_list(
    line_list: List[str], url_prefix: str = URL_PREFIX
) -> List[Tuple[str, str]]:
    """추천수(L:)가 40 초과인 항목만 제목/링크를 짝지어 (link, title) 목록을 만든다."""
    state = 0
    title = ""
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<div class="like-value">L:(?P<like_count>\d+)</div>', line)
            if m:
                like_count = int(m.group("like_count"))
                if like_count > 40:
                    state = 1
                else:
                    state = 0
        elif state == 1:
            m = re.search(r"<div>(?P<title>.+)</div>", line)
            if m:
                title = m.group("title")
                state = 2
        elif state == 2:
            m = re.search('<a href="(?P<link>[^"]+)"[^>]*>', line)
            if m:
                link = url_prefix + m.group("link")
                result_list.append((link, title))
                state = 0
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

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- parse_feed_list ---

            def _entry(self, like, title, link):
                return [
                    f'<div class="like-value">L:{like}</div>',
                    f"<div>{title}</div>",
                    f'<a href="{link}">',
                ]

            def test_parse_feed_list_includes_high_like(self):
                lines = self._entry(41, "Popular", "/post/1")
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://mmzone.co.kr/post/1", "Popular")],
                )

            def test_parse_feed_list_skips_low_like(self):
                lines = self._entry(40, "Unpopular", "/post/2")
                self.assertEqual(parse_feed_list(lines), [])

            def test_parse_feed_list_multiple(self):
                lines = self._entry(50, "A", "/a") + self._entry(99, "B", "/b")
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["A", "B"])

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
