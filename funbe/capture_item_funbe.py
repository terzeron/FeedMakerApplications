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
    """g5_url → view_list 링크 → content__title → 제목 순으로 상태머신을 돌려 (link, title) 목록을 만든다."""
    link = ""
    url_prefix = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'var\s+g5_url\s+=\s+"(?P<url_prefix>[^"]+)";', line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(
                r'<td[^>]*name="view_list"[^>]*data-role="(?P<link>[^"]+)">', line
            )
            if m:
                link = m.group("link")
                link = re.sub(r"&amp;", "&", link)
                link = url_prefix + link
                state = 2
        elif state == 2:
            m = re.search(r'<td[^>]*class="content__title"', line)
            if m:
                state = 3
        elif state == 3:
            m = re.search(r"\s*(?P<title>\S[^<>]*)(?:</td>)?\s*", line)
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

        class TestCaptureItemFunbe(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "8"]), 8)

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "."]), 1000)

            # --- parse_feed_list ---

            def _page(self, items):
                lines = ['var g5_url = "https://funbe.test";']
                for link, title in items:
                    lines.append(f'<td name="view_list" data-role="{link}">')
                    lines.append('<td class="content__title">')
                    lines.append(f"  {title}</td>")
                return lines

            def test_parse_feed_list_basic(self):
                lines = self._page([("/page/1", "1화")])
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://funbe.test/page/1", "1화")],
                )

            def test_parse_feed_list_unescapes_amp(self):
                lines = self._page([("/page/1&amp;x=2", "T")])
                self.assertEqual(
                    parse_feed_list(lines)[0][0], "https://funbe.test/page/1&x=2"
                )

            def test_parse_feed_list_multiple(self):
                lines = self._page([("/p/1", "A"), ("/p/2", "B")])
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["A", "B"])

            def test_parse_feed_list_requires_g5_url(self):
                lines = [
                    '<td name="view_list" data-role="/p/1">',
                    '<td class="content__title">',
                    "  T</td>",
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

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://funbe642.com/절세무신 을 받아온 실제 HTML 중 파서가 매칭하는
            #       영역(g5_url + view_list/content__title/제목 블록 3개)만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_funbe.py -n 5'로 직접 실행해 캡처한 결과(제목 뒤 탭 포함).
            REAL_SAMPLE_LINES = [
                'var g5_url       = "https://funbe642.com";',
                '\t\t\t\t<td width="2%" name="view_list" data-role="/절세무신_720화.html">',
                '\t\t\t\t<td style="padding: 2%;" class="content__title" name="view_list" data-role="/절세무신_720화.html" alt="절세무신 720화"> ',
                "\t\t\t\t\t절세무신 720화\t\t\t\t</td>",
                '\t\t\t\t<td width="2%" name="view_list" data-role="/절세무신_719화.html">',
                '\t\t\t\t<td style="padding: 2%;" class="content__title" name="view_list" data-role="/절세무신_719화.html" alt="절세무신 719화"> ',
                "\t\t\t\t\t절세무신 719화\t\t\t\t</td>",
                '\t\t\t\t<td width="2%" name="view_list" data-role="/절세무신_718화.html">',
                '\t\t\t\t<td style="padding: 2%;" class="content__title" name="view_list" data-role="/절세무신_718화.html" alt="절세무신 718화"> ',
                "\t\t\t\t\t절세무신 718화\t\t\t\t</td>",
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_LINES)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://funbe642.com/절세무신_720화.html\t003. 절세무신 720화\t\t\t\t",
                        "https://funbe642.com/절세무신_719화.html\t002. 절세무신 719화\t\t\t\t",
                        "https://funbe642.com/절세무신_718화.html\t001. 절세무신 718화\t\t\t\t",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
