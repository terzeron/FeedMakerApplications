#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "https://www.mmzone.co.kr"


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
    """list-title-text 제목과 mt_view 링크를 짝지어 (link, title) 목록을 만든다."""
    state = 0
    title = ""
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(
                r'<div class="list-title-text"[^>]*title="(?P<title>[^"]*)"', line
            )
            if m:
                title = m.group("title")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>/mms_tool/mt_view\.php\?id=\d+)"', line)
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

            def test_parse_feed_list_basic(self):
                lines = [
                    '<div class="list-title-text" title="My Kit">',
                    '<a href="/mms_tool/mt_view.php?id=42">',
                ]
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://www.mmzone.co.kr/mms_tool/mt_view.php?id=42", "My Kit")],
                )

            def test_parse_feed_list_requires_title_first(self):
                lines = ['<a href="/mms_tool/mt_view.php?id=42">']
                self.assertEqual(parse_feed_list(lines), [])

            def test_parse_feed_list_multiple(self):
                lines = [
                    '<div class="list-title-text" title="A">',
                    '<a href="/mms_tool/mt_view.php?id=1">',
                    '<div class="list-title-text" title="B">',
                    '<a href="/mms_tool/mt_view.php?id=2">',
                ]
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

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 www.mmzone.co.kr mms_tool(거래장터) 페이지에서 파서가 매칭하는
            #       영역(list-title-text div + mt_view anchor) 3개만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_link_title.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '                                     <div class="list-title-text" style="color:var(--theme-title-text)" title="창고정리중 에어로 미조립키트 판매합니다.">',
                '                               <a href="/mms_tool/mt_view.php?id=263484" class="link-block cover-abs"></a>',
                '                                     <div class="list-title-text" style="color:var(--theme-title-text)" title="M4A3E8 2026 하비페어 한정판 삽니다.">',
                '                               <a href="/mms_tool/mt_view.php?id=263483" class="link-block cover-abs"></a>',
                '                                     <div class="list-title-text" style="color:var(--theme-title-text)" title="반다이 에반게리온 판매합니다.">',
                '                               <a href="/mms_tool/mt_view.php?id=263482" class="link-block cover-abs"></a>',
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_LINES)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://www.mmzone.co.kr/mms_tool/mt_view.php?id=263484\t창고정리중 에어로 미조립키트 판매합니다.",
                        "https://www.mmzone.co.kr/mms_tool/mt_view.php?id=263483\tM4A3E8 2026 하비페어 한정판 삽니다.",
                        "https://www.mmzone.co.kr/mms_tool/mt_view.php?id=263482\t반다이 에반게리온 판매합니다.",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
