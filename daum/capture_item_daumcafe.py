#!/usr/bin/env python

import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


LINK_PREFIX = "http://cafe.daum.net/_c21_/"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def parse_feed_list(line_list: List[str]) -> List[Tuple[str, str]]:
    """GRPCODE/GRPID/FLDID를 모은 뒤 bbs_read 링크와 제목을 추출해 (link, title) 목록을 만든다."""
    cafe_name = ""
    cafe_id = ""
    board_name = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'GRPCODE\s*:\s*"(?P<cafe_name>[^"]+)"', line)
            if m:
                cafe_name = m.group("cafe_name")
            m = re.search(r'GRPID\s*:\s*"(?P<cafe_id>[^"]+)"', line)
            if m:
                cafe_id = m.group("cafe_id")
            m = re.search(r'FLDID\s*:\s*"(?P<board_name>[^"]+)"', line)
            if m:
                board_name = m.group("board_name")
            if cafe_name != "" and cafe_id != "" and board_name != "":
                state = 1
        elif state == 1:
            m = re.search(
                r'<a[^>]*href="[^"]+/bbs_read[^"]*datanum=(?P<article_id>\d+)[^>]*>(?P<title>.+)</a>',
                line,
            )
            if m:
                link = (
                    LINK_PREFIX
                    + "bbs_read?"
                    + "&fldid="
                    + board_name
                    + "&grpid="
                    + cafe_id
                    + "&datanum="
                    + m.group("article_id")
                )
                title = m.group("title")
                title = re.sub(r"(<[^>]*?>|^\s+|\s+$)", "", title)
                if link and title:
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

    line_list = IO.read_stdin_as_line_list()
    result_list = parse_feed_list(line_list)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemDaumcafe(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 30)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "9"]), 9)

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "."]), 30)

            # --- parse_feed_list ---

            def _header(self):
                return [
                    'GRPCODE : "mycafe"',
                    'GRPID : "100"',
                    'FLDID : "board"',
                ]

            def test_parse_feed_list_basic(self):
                lines = self._header() + [
                    '<a class="x" href="/c/bbs_read?datanum=55">Hello</a>',
                ]
                self.assertEqual(
                    parse_feed_list(lines),
                    [
                        (
                            "http://cafe.daum.net/_c21_/bbs_read?&fldid=board&grpid=100&datanum=55",
                            "Hello",
                        )
                    ],
                )

            def test_parse_feed_list_strips_inner_tags_and_whitespace(self):
                lines = self._header() + [
                    '<a href="/c/bbs_read?datanum=1">  <b>Bold</b>Title  </a>',
                ]
                # 모든 내부 태그와 양끝 공백이 제거된다
                self.assertEqual(parse_feed_list(lines)[0][1], "BoldTitle")

            def test_parse_feed_list_requires_all_three_ids(self):
                # GRPCODE/GRPID/FLDID 중 하나라도 빠지면 링크를 수집하지 않는다
                lines = [
                    'GRPCODE : "mycafe"',
                    'GRPID : "100"',
                    '<a href="/c/bbs_read?datanum=1">Hello</a>',
                ]
                self.assertEqual(parse_feed_list(lines), [])

            def test_parse_feed_list_multiple(self):
                lines = self._header() + [
                    '<a href="/c/bbs_read?datanum=1">A</a>',
                    '<a href="/c/bbs_read?datanum=2">B</a>',
                ]
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["A", "B"])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 30), ["l1\tA", "l2\tB"]
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 30), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
