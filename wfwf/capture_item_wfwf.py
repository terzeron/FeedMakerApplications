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
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def parse_feed_list(line_list: List[str]) -> List[Tuple[str, str]]:
    """og:url로 url prefix를 잡은 뒤 anchor/subject를 상태머신으로 추적해 (link, title) 목록을 만든다."""
    link = ""
    url_prefix = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(
                r'<meta property="og:url" content="(?P<url_prefix>https?://[^/]+)[^"]*"\s*/?>',
                line,
            )
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(
                r'<a(?:[^>]*)href="(?P<link>/[^"]*)&(amp;)?title=[^"]*"', line
            )
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r"&amp;", "&", link)
                state = 2
        elif state == 2:
            m = re.search(r'<div class="subject">\s*(?P<title>[^<]+)\s*<', line)
            if m:
                title = m.group("title")
                title = re.sub(r"\s+", " ", title)
                title = re.sub(r"&nbsp;", " ", title)
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

        class TestCaptureItemWfwf(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "feed.xml"]), 1000)

            def test_parse_args_combined(self):
                self.assertEqual(parse_args(["-f", ".", "-n", "3"]), 3)

            # --- parse_feed_list ---

            def _page(self, items):
                lines = [
                    '<meta property="og:url" content="https://wfwf.test/list?id=1" />'
                ]
                for link, title in items:
                    lines.append(f'<a class="x" href="{link}&title=foo">')
                    lines.append(f'<div class="subject"> {title} <span>')
                return lines

            def test_parse_feed_list_basic(self):
                lines = self._page([("/cartoon/100", "Title One")])
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://wfwf.test/cartoon/100", "Title One ")],
                )

            def test_parse_feed_list_multiple(self):
                lines = self._page([("/c/1", "T1"), ("/c/2", "T2")])
                self.assertEqual(
                    parse_feed_list(lines),
                    [
                        ("https://wfwf.test/c/1", "T1 "),
                        ("https://wfwf.test/c/2", "T2 "),
                    ],
                )

            def test_parse_feed_list_unescapes_amp_in_link(self):
                lines = [
                    '<meta property="og:url" content="https://wfwf.test/list" />',
                    '<a href="/c/1&amp;x=2&title=foo">',
                    '<div class="subject"> T <span>',
                ]
                self.assertEqual(
                    parse_feed_list(lines), [("https://wfwf.test/c/1&x=2", "T ")]
                )

            def test_parse_feed_list_collapses_title_whitespace(self):
                lines = [
                    '<meta property="og:url" content="https://wfwf.test/list" />',
                    '<a href="/c/1&title=foo">',
                    '<div class="subject">  Hello   World&nbsp;! <span>',
                ]
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://wfwf.test/c/1", "Hello World ! ")],
                )

            def test_parse_feed_list_no_meta_returns_empty(self):
                lines = ['<a href="/c/1&title=foo">', '<div class="subject"> T <span>']
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
                # 전체 3개 기준으로 번호를 매기되 상위 2개만 출력
                self.assertEqual(render_lines(result, 2), ["l1\t003. A", "l2\t002. B"])

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 list_url(https://wfwf462.com/cl?toon=10543)을
            #       받아온 실제 HTML 중 파서가 매칭하는 영역(og:url meta + anchor/subject
            #       블록 3개)만 샘플링한 것.
            # 기대 출력: 동일 입력을 'capture_item_wfwf.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '<meta property="og:url" content="https://wfwf462.com/cl?toon=10543">',
                '                    <a href="/cv?toon=10543&num=120&title=고블린슬레이어107화" class="view_open">',
                '                        <div class="list-box">',
                '                            <div class="num">120</div>',
                '                            <div class="subject">고블린 슬레이어 107화&nbsp;</div>',
                '                    <a href="/cv?toon=10543&num=119&title=고블린슬레이어106화" class="view_open">',
                '                        <div class="list-box">',
                '                            <div class="num">119</div>',
                '                            <div class="subject">고블린 슬레이어 106화&nbsp;</div>',
                '                    <a href="/cv?toon=10543&num=118&title=고블린슬레이어105화" class="view_open">',
                '                        <div class="list-box">',
                '                            <div class="num">118</div>',
                '                            <div class="subject">고블린 슬레이어 105화&nbsp;</div>',
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_LINES)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://wfwf462.com/cv?toon=10543&num=120\t003. 고블린 슬레이어 107화 ",
                        "https://wfwf462.com/cv?toon=10543&num=119\t002. 고블린 슬레이어 106화 ",
                        "https://wfwf462.com/cv?toon=10543&num=118\t001. 고블린 슬레이어 105화 ",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
