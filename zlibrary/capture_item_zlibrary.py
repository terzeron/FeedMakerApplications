#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "https://kr1lib.org"
EXCLUSION_PATTERN = r"(한국어|grammar|korean|vocabular|어휘|문법|topik)"


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
    """book anchor에서 (link, title)을 뽑되, 한국어 학습서 등 제외 키워드 제목은 건너뛴다."""
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        m = re.search(
            r'<a href="(?P<link>/book/[^"]+)" style="[^"]*underline[^"]*">(?P<title>[^<]+)</a>',
            line,
        )
        if m:
            link = url_prefix + m.group("link")
            title = m.group("title")
            if re.search(EXCLUSION_PATTERN, title, re.IGNORECASE):
                continue
            result_list.append((link, title))
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

        class TestCaptureItemZlibrary(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- parse_feed_list ---

            def _anchor(self, link, title):
                return (
                    f'<a href="{link}" style="text-decoration: underline">{title}</a>'
                )

            def test_parse_feed_list_basic(self):
                lines = [self._anchor("/book/123/abc", "Great Novel")]
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://kr1lib.org/book/123/abc", "Great Novel")],
                )

            def test_parse_feed_list_excludes_korean_keyword(self):
                lines = [self._anchor("/book/1", "한국어 문법")]
                self.assertEqual(parse_feed_list(lines), [])

            def test_parse_feed_list_excludes_english_keyword_case_insensitive(self):
                lines = [self._anchor("/book/1", "English GRAMMAR Guide")]
                self.assertEqual(parse_feed_list(lines), [])

            def test_parse_feed_list_keeps_unrelated(self):
                lines = [
                    self._anchor("/book/1", "Science Fiction"),
                    self._anchor("/book/2", "topik study"),
                ]
                self.assertEqual(
                    [t for _, t in parse_feed_list(lines)], ["Science Fiction"]
                )

            def test_parse_feed_list_requires_underline_style(self):
                lines = ['<a href="/book/1" style="color:red">No Underline</a>']
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
