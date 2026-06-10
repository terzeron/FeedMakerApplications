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
    """og:url → toon anchor → subject 제목 순으로 상태머신을 돌려 (link, title) 목록을 만든다."""
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
            m = re.search(r'<a\s*href="(?P<link>/\w+\d+\?toon[^"]*)">', line)
            if m:
                link = url_prefix + m.group("link")
                state = 2
        elif state == 2:
            m = re.search(
                r'<div class="subject">\s*(?:<div class=\'[^\']+\'><span class=\'text\'>.*</span></div>)?(?P<title>[^<]+)\s*<',
                line,
            )
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

        class TestCaptureItemWtwt(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- parse_feed_list ---

            def _page(self, items):
                lines = ['<meta property="og:url" content="https://wtwt.test/x" />']
                for link, title in items:
                    lines.append(f'<a href="{link}">')
                    lines.append(f'<div class="subject"> {title} <span>')
                return lines

            def test_parse_feed_list_basic(self):
                lines = self._page([("/abc123?toon=1", "Title One")])
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://wtwt.test/abc123?toon=1", "Title One ")],
                )

            def test_parse_feed_list_collapses_whitespace(self):
                lines = self._page([("/abc1?toon", "Hello   World&nbsp;!")])
                self.assertEqual(parse_feed_list(lines)[0][1], "Hello World ! ")

            def test_parse_feed_list_multiple(self):
                lines = self._page([("/a1?toon", "A"), ("/b2?toon", "B")])
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["A ", "B "])

            def test_parse_feed_list_requires_og_url(self):
                lines = ['<a href="/a1?toon">', '<div class="subject"> T <span>']
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
            # 입력: crawler.py(--encoding=cp949)로 https://wtwt329.com/v1?toon=7094 를 받아온 실제 HTML 중
            #       파서가 매칭하는 영역(og:url + toon anchor/subject 블록 3개)만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_wtwt.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '<meta property="og:url" content="https://wtwt329.com">',
                '                    <a href="/v2?toon=7094&num=263">',
                '                            <div class="subject">261화 - 후기</div>',
                '                    <a href="/v2?toon=7094&num=262">',
                '                            <div class="subject">260화 -마지막 화-</div>',
                '                    <a href="/v2?toon=7094&num=261">',
                '                            <div class="subject">259화</div>',
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_LINES)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://wtwt329.com/v2?toon=7094&num=263\t003. 261화 - 후기",
                        "https://wtwt329.com/v2?toon=7094&num=262\t002. 260화 -마지막 화-",
                        "https://wtwt329.com/v2?toon=7094&num=261\t001. 259화",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
