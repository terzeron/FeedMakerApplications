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


def parse_feed_list(line_list: List[str]) -> List[Tuple[str, str]]:
    """og:url → content__title 링크 → 제목 순으로 상태머신을 돌려 (link, title) 목록을 만든다."""
    link = ""
    url_prefix = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(
                r'<meta property="og:url" content="(?P<url_prefix>https?://[^"/]+)[^"]*"\s*/?>',
                line,
            )
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(
                r'<td[^>]*class="content__title"[^>]*data-role="(?P<link>[^"]+)"[^>]*>',
                line,
            )
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r"&amp;", "&", link)
                state = 2
        elif state == 2:
            m = re.search(r"\s*(?P<title>\S+)\s*</td>", line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1
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

        class TestCaptureItemToonkor(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- parse_feed_list ---

            def _page(self, items):
                lines = ['<meta property="og:url" content="https://toonkor.test/x" />']
                for link, title in items:
                    lines.append(f'<td class="content__title" data-role="{link}">')
                    lines.append(f"  {title} </td>")
                return lines

            def test_parse_feed_list_basic(self):
                lines = self._page([("/page/1", "1화")])
                self.assertEqual(
                    parse_feed_list(lines), [("https://toonkor.test/page/1", "1화")]
                )

            def test_parse_feed_list_unescapes_amp(self):
                lines = self._page([("/page/1&amp;x=2", "T")])
                self.assertEqual(
                    parse_feed_list(lines)[0][0], "https://toonkor.test/page/1&x=2"
                )

            def test_parse_feed_list_multiple(self):
                lines = self._page([("/p/1", "A"), ("/p/2", "B")])
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["A", "B"])

            def test_parse_feed_list_requires_og_url(self):
                lines = [
                    '<td class="content__title" data-role="/p/1">',
                    "  T </td>",
                ]
                self.assertEqual(parse_feed_list(lines), [])

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
