#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "http://terms.naver.com/"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def parse_feed_list(
    line_list: List[str], url_prefix: str = URL_PREFIX
) -> List[Tuple[str, str]]:
    """title 마커 다음의 entry.naver anchor에서 (link, title)을 추출."""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<strong class="title">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(
                r'<a href="/(?P<url>entry\.naver\?[^"]+)"[^>]*>(?P<title>[^<]+)</a>',
                line,
            )
            if m:
                url = m.group("url")
                url = re.sub(r"&amp;", "&", url)
                title = m.group("title")
                link = url_prefix + url
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

        class TestCaptureItemNavercast(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 30)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "7"]), 7)

            # --- parse_feed_list ---

            def test_parse_feed_list_basic(self):
                lines = [
                    '<strong class="title">',
                    '<a href="/entry.naver?docId=1&amp;x=2">My Title</a>',
                ]
                self.assertEqual(
                    parse_feed_list(lines),
                    [("http://terms.naver.com/entry.naver?docId=1&x=2", "My Title")],
                )

            def test_parse_feed_list_requires_title_marker(self):
                lines = ['<a href="/entry.naver?docId=1">T</a>']
                self.assertEqual(parse_feed_list(lines), [])

            def test_parse_feed_list_multiple(self):
                lines = [
                    '<strong class="title">',
                    '<a href="/entry.naver?docId=1">A</a>',
                    '<strong class="title">',
                    '<a href="/entry.naver?docId=2">B</a>',
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

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://terms.naver.com/list.naver?cid=58737&categoryId=58737 을
            #       받아온 실제 HTML 중 파서가 매칭하는 (strong.title + a.entry.naver) 블록 3개만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_navercast.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '\t\t\t\t\t<strong class="title">',
                "\t\t\t\t\t\t<a href=\"/entry.naver?docId=6917568&cid=59011&categoryId=59011\" onclick=\"nclk(this, 'tml.termlist', '', '', 1);\">이재유 · 김사국 · 강주룡 [李載裕 · 金恩國 · 姜周龍]</a>",
                '\t\t\t\t\t<strong class="title">',
                "\t\t\t\t\t\t<a href=\"/entry.naver?docId=6916298&cid=59011&categoryId=59011\" onclick=\"nclk(this, 'tml.termlist', '', '', 1);\">이명균 · 장석영 · 유진태 [李明均 · 張錫英 · 兪鎭泰]</a>",
                '\t\t\t\t\t<strong class="title">',
                "\t\t\t\t\t\t<a href=\"/entry.naver?docId=6915924&cid=59011&categoryId=59011\" onclick=\"nclk(this, 'tml.termlist', '', '', 1);\">이선경 · 조화벽 · 김향화 [李善卿 · 趙和璧 · 金香花]</a>",
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_LINES)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "http://terms.naver.com/entry.naver?docId=6917568&cid=59011&categoryId=59011\t이재유 · 김사국 · 강주룡 [李載裕 · 金恩國 · 姜周龍]",
                        "http://terms.naver.com/entry.naver?docId=6916298&cid=59011&categoryId=59011\t이명균 · 장석영 · 유진태 [李明均 · 張錫英 · 兪鎭泰]",
                        "http://terms.naver.com/entry.naver?docId=6915924&cid=59011&categoryId=59011\t이선경 · 조화벽 · 김향화 [李善卿 · 趙和璧 · 金香花]",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
