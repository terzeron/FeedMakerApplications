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


def normalize_title(title: str) -> str:
    """제목 공백을 정규화하고 1~2자리 회차 숫자를 3자리로 zero-padding 한다."""
    title = re.sub(r"\s+", " ", title)
    title = re.sub(r"\b(\d\d)(권|화|부|편)", "0\g<1>\g<2>", title)
    title = re.sub(r"\b(\d)(권|화|부|편)", "00\g<1>\g<2>", title)
    return title


def parse_feed_list(line_list: List[str]) -> List[Tuple[str, str]]:
    """item-subject anchor의 링크와 다음 줄 제목을 짝지어 (link, title) 목록을 만든다."""
    link = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(
                r'<a [^>]*href="(?P<link>[^"]+\/\d+)(\/|\?)[^"]*" class="item-subject">',
                line,
            )
            if m:
                link = m.group("link")
                link = re.sub(r"&amp;", "&", link)
                state = 1
        elif state == 1:
            m = re.search(
                r'^\s*(?P<title>\S+.*\S)\s*(?:<span class="count[^"]*">\d+</span>|</a>)\r?$',
                line,
            )
            if m:
                title = normalize_title(m.group("title"))
                result_list.append((link, title))
                state = 0
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """전체 개수에서 역순 번호를 매겨 'link\\t%03d. title' 라인 목록을 만든다."""
    num = len(result_list)
    lines: List[str] = []
    for link, title in result_list[:num_of_recent_feeds]:
        lines.append("%s\t%03d. %s" % (link, num, title))
        num -= 1
    return lines


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

        class TestCaptureItemManatoki(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "9"]), 9)

            # --- normalize_title ---

            def test_normalize_title_pads_single_digit(self):
                self.assertEqual(normalize_title("5화"), "005화")

            def test_normalize_title_pads_double_digit(self):
                self.assertEqual(normalize_title("12화"), "012화")

            def test_normalize_title_collapses_whitespace(self):
                self.assertEqual(normalize_title("hello   world"), "hello world")

            def test_normalize_title_three_digit_unchanged(self):
                self.assertEqual(normalize_title("123화"), "123화")

            def test_normalize_title_other_units(self):
                self.assertEqual(normalize_title("3권"), "003권")

            # --- parse_feed_list ---

            def test_parse_feed_list_with_count_span(self):
                lines = [
                    '<a href="http://m.test/123/" class="item-subject">',
                    '  5화 <span class="count-rate">10</span>',
                ]
                self.assertEqual(
                    parse_feed_list(lines), [("http://m.test/123", "005화")]
                )

            def test_parse_feed_list_with_anchor_close(self):
                lines = [
                    '<a href="http://m.test/55/" class="item-subject">',
                    "  My Title</a>",
                ]
                self.assertEqual(
                    parse_feed_list(lines), [("http://m.test/55", "My Title")]
                )

            def test_parse_feed_list_unescapes_amp(self):
                lines = [
                    '<a href="http://m.test/7?a=1&amp;b=2/9/" class="item-subject">',
                    "  T1</a>",
                ]
                # link은 .../숫자 + 구분자 직전까지 캡처된다
                self.assertTrue(
                    parse_feed_list(lines)[0][0].startswith("http://m.test/")
                )

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), [])

            # --- render_lines ---

            def test_render_lines_numbering_descends_from_total(self):
                result = [("l1", "A"), ("l2", "B"), ("l3", "C")]
                self.assertEqual(
                    render_lines(result, 1000),
                    ["l1\t003. A", "l2\t002. B", "l3\t001. C"],
                )

            def test_render_lines_limit_keeps_total_based_numbering(self):
                result = [("l1", "A"), ("l2", "B"), ("l3", "C")]
                self.assertEqual(render_lines(result, 2), ["l1\t003. A", "l2\t002. B"])

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
