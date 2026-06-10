#!/usr/bin/env python


import os
import sys
import re
import getopt
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


def clean_title(title: str) -> str:
    """제목에서 HTML 태그 꼬리와 '[email protected]' 잔재를 제거한다."""
    title = re.sub(r"\s*</?\w+[^>]*>", "", title)
    title = re.sub(r"\s*\[email&#160;protected\]", "", title)
    return title


def parse_feed_list(line_list: List[str]) -> List[Tuple[str, str]]:
    """og:url → sub_title → /topic 링크 → 제목 순으로 상태머신을 돌려 (link, title) 목록을 만든다."""
    url_prefix = ""
    link = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(
                r'<meta property="og:url" content="(?P<url_prefix>https://torrentsee[^"]+\.com)/[^"]*"/>',
                line,
            )
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div class="\s*sub_title\s*">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'^\s*<a href="(?P<link>/topic/\d+)">\s*$', line)
            if m:
                link = url_prefix + m.group("link")
                state = 3
        elif state == 3:
            m = re.search(r"^\s*(?P<title>.+?)\s*(</?\w+[^>]*>)?$", line)
            if m:
                title = clean_title(m.group("title"))
                result_list.append((link, title))
                state = 2
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """(link, title) 목록을 'link\\ttitle' 라인 목록으로 변환."""
    return [
        "%s\t%s" % (link, title) for (link, title) in result_list[:num_of_recent_feeds]
    ]


def main() -> int:
    num_of_recent_feeds = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()
    result_list = parse_feed_list(line_list)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemTorrentsee(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- clean_title ---

            def test_clean_title_removes_tag_tail(self):
                self.assertEqual(clean_title("Hello <span>"), "Hello")

            def test_clean_title_removes_email_protected(self):
                self.assertEqual(clean_title("Title [email&#160;protected]"), "Title")

            def test_clean_title_plain(self):
                self.assertEqual(clean_title("Just Text"), "Just Text")

            # --- parse_feed_list ---

            def _page(self, items):
                lines = [
                    '<meta property="og:url" content="https://torrentsee123.com/list"/>'
                ]
                for link, title in items:
                    lines.append('<div class="sub_title">')
                    lines.append(f'<a href="{link}">')
                    lines.append(f"   {title}")
                return lines

            def test_parse_feed_list_basic(self):
                lines = self._page([("/topic/55", "My Topic")])
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://torrentsee123.com/topic/55", "My Topic")],
                )

            def test_parse_feed_list_multiple(self):
                lines = self._page([("/topic/1", "A B"), ("/topic/2", "C D")])
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["A B", "C D"])

            def test_parse_feed_list_requires_og_url(self):
                lines = [
                    '<div class="sub_title">',
                    '<a href="/topic/1">',
                    "   T",
                ]
                self.assertEqual(parse_feed_list(lines), [])

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
