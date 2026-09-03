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
    """data-chapter-list 컨테이너 → chapter 링크 → 제목 순으로 상태머신을 돌려 (link, title) 목록을 만든다.
    페이지에 동일한 회차 목록이 두 번(모바일 시트 + 본문) 중복 렌더링되므로,
    첫 번째 data-chapter-list 컨테이너만 파싱하고 두 번째가 나오면 멈춘다."""
    link = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            if 'data-chapter-list=""' in line:
                state = 1
        elif state == 1:
            if 'data-chapter-list=""' in line:
                break
            m = re.search(
                r'<a href="(?P<link>https://[^"]+)" data-chapter-id="\d+" class="chapter-item[^"]*">',
                line,
            )
            if m:
                link = m.group("link")
                state = 2
        elif state == 2:
            m = re.search(
                r'<span class="min-w-0 truncate text-\[13px\] font-semibold">(?P<title>[^<]+)</span>',
                line,
            )
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

        class TestCaptureItemXtoon(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- parse_feed_list ---

            def _page(self, items, duplicate=True):
                lines = ['<div class="flex flex-col" data-chapter-list="">']
                for link, title in items:
                    lines.append(
                        f'<a href="{link}" data-chapter-id="1" class="chapter-item flex">'
                    )
                    lines.append(
                        f'<span class="min-w-0 truncate text-[13px] font-semibold">{title}</span>'
                    )
                if duplicate:
                    lines.append(
                        '<div class="mt-4 flex flex-col" data-chapter-list="">'
                    )
                    for link, title in items:
                        lines.append(
                            f'<a href="{link}" data-chapter-id="1" class="chapter-item flex">'
                        )
                        lines.append(
                            f'<span class="min-w-0 truncate text-[13px] font-semibold">{title}</span>'
                        )
                return lines

            def test_parse_feed_list_basic(self):
                lines = self._page(
                    [("https://xtoon.test/comics/1/chapters/10", "10화")]
                )
                self.assertEqual(
                    parse_feed_list(lines),
                    [("https://xtoon.test/comics/1/chapters/10", "10화")],
                )

            def test_parse_feed_list_multiple(self):
                lines = self._page(
                    [
                        ("https://xtoon.test/comics/1/chapters/2", "2화"),
                        ("https://xtoon.test/comics/1/chapters/1", "1화"),
                    ]
                )
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["2화", "1화"])

            def test_parse_feed_list_ignores_duplicate_container(self):
                lines = self._page([("https://xtoon.test/comics/1/chapters/1", "1화")])
                self.assertEqual(len(parse_feed_list(lines)), 1)

            def test_parse_feed_list_requires_chapter_list_marker(self):
                lines = [
                    '<a href="https://xtoon.test/comics/1/chapters/1" data-chapter-id="1" class="chapter-item flex">',
                    '<span class="min-w-0 truncate text-[13px] font-semibold">1화</span>',
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
            # 입력: crawler.py(--render-js=true)로 https://newxtoon1.com/comics/9818 을 받아온 실제 HTML 중
            #       파서가 매칭하는 영역(data-chapter-list + chapter anchor/제목 3개, 중복 컨테이너 1개 포함)만 샘플링.
            #       (2026-09 xtoon 사이트가 t3.xtoon365.com에서 newxtoon1.com으로 리뉴얼되며 마크업이 전면 교체됨)
            # 기대 출력: 동일 입력을 'capture_item_xtoon.py -n 2'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '                    <div class="flex flex-col" data-chapter-list="">',
                '                        <a href="https://newxtoon1.com/comics/9818/chapters/801302" data-chapter-id="801302" class="chapter-item flex min-h-[58px] items-center gap-3 border-b border-line py-3">',
                '                    <span class="min-w-0 truncate text-[13px] font-semibold">54화(시즌 1 완결)</span>',
                '                <a href="https://newxtoon1.com/comics/9818/chapters/801301" data-chapter-id="801301" class="chapter-item flex min-h-[58px] items-center gap-3 border-b border-line py-3">',
                '                    <span class="min-w-0 truncate text-[13px] font-semibold">53화</span>',
                '                    <div class="mt-4 flex flex-col overflow-hidden rounded-[12px] border border-line bg-surface" data-chapter-list="">',
                '                        <a href="https://newxtoon1.com/comics/9818/chapters/801302" data-chapter-id="801302" class="chapter-item flex min-h-[58px] items-center gap-3 border-b border-line py-3">',
                '                    <span class="min-w-0 truncate text-[13px] font-semibold">54화(시즌 1 완결)</span>',
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_LINES)
                lines = render_lines(result, 2)
                self.assertEqual(
                    lines,
                    [
                        "https://newxtoon1.com/comics/9818/chapters/801302\t002. 54화(시즌 1 완결)",
                        "https://newxtoon1.com/comics/9818/chapters/801301\t001. 53화",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
