#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, NamedTuple

from bin.feed_maker_util import IO


class Feed(NamedTuple):
    link: str
    title: str
    body: str


def parse_args(argv: List[str]) -> tuple[int, List[str]]:
    num_of_recent_feeds = 20
    exclude_keywords: List[str] = []

    optlist, _ = getopt.getopt(argv, "f:n:x:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-x":
            exclude_keywords = [kw.strip() for kw in a.split(",") if kw.strip()]

    return num_of_recent_feeds, exclude_keywords


def strip_tags(line: str) -> str:
    return re.sub(r"<[^>]+>", "", line).strip()


def parse_feed_list(line_list: List[str]) -> List[Feed]:
    feeds: List[Feed] = []
    seen_links: set[str] = set()

    link = None
    title = None
    body_parts: List[str] = []
    in_h2 = False
    in_body = False

    def finalize() -> None:
        nonlocal link, title, body_parts, in_h2, in_body
        if link and title and link not in seen_links:
            seen_links.add(link)
            feeds.append(Feed(link, title, " ".join(body_parts).strip()))
        link = None
        title = None
        body_parts = []
        in_h2 = False
        in_body = False

    for line in line_list:
        # <a href="/blog/@username/9698/" class="block">
        m = re.search(r'<a\s+href="(/blog/@[^"]+/\d+/)"[^>]*class="block"', line)
        if m:
            finalize()
            link = "https://wikidocs.net" + m.group(1)
            continue

        if not link:
            continue

        if title is None:
            # <h2 class="text-xl font-bold ...">
            if not in_h2:
                if re.search(r'<h2[^>]*class="text-xl font-bold', line):
                    in_h2 = True
                    # 제목이 같은 줄에 함께 있을 수도 있다
                    text = strip_tags(line)
                    if text:
                        title = text
                        in_h2 = False
                continue
            text = strip_tags(line)
            if text:
                title = text
                in_h2 = False
            continue

        # <p class="... break-words"> ... 본문 excerpt ... </p>
        if not in_body:
            if re.search(r"<p[^>]*break-words", line):
                in_body = True
                text = strip_tags(line)
                if text:
                    body_parts.append(text)
                if "</p>" in line:
                    finalize()
            continue

        if "</p>" in line:
            text = strip_tags(line)
            if text:
                body_parts.append(text)
            finalize()
            continue
        text = strip_tags(line)
        if text:
            body_parts.append(text)

    finalize()
    return feeds


def filter_excluded(feeds: List[Feed], exclude_keywords: List[str]) -> List[Feed]:
    if not exclude_keywords:
        return feeds

    result: List[Feed] = []
    for feed in feeds:
        haystack = f"{feed.title} {feed.body}"
        if any(keyword in haystack for keyword in exclude_keywords):
            continue
        result.append(feed)
    return result


def print_feeds(feeds: List[Feed], limit: int) -> None:
    for feed in feeds[:limit]:
        print(f"{feed.link}\t{feed.title}")


def main() -> int:
    num_of_recent_feeds, exclude_keywords = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()
    feeds = parse_feed_list(line_list)
    feeds = filter_excluded(feeds, exclude_keywords)
    print_feeds(feeds, num_of_recent_feeds)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import io
        import contextlib
        import unittest

        def card(link: str, title_lines: List[str], body_lines: List[str]) -> List[str]:
            """리스트 페이지의 카드 하나에 해당하는 HTML 라인 목록을 만든다."""
            lines = [f'<a href="{link}" class="block">']
            lines.append(
                '<h2 class="text-xl font-bold text-gray-800 dark:text-gray-200">'
            )
            lines.extend(title_lines)
            lines.append("</h2>")
            if body_lines is not None:
                lines.append(
                    '<p class="text-gray-600 dark:text-gray-400 mt-2 break-words">'
                )
                lines.extend(body_lines)
                lines.append("</p>")
            return lines

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_defaults(self):
                self.assertEqual(parse_args([]), (20, []))

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), (5, []))

            def test_parse_args_exclude_single(self):
                self.assertEqual(parse_args(["-x", "AD"]), (20, ["AD"]))

            def test_parse_args_exclude_multiple(self):
                self.assertEqual(
                    parse_args(["-x", "AD,PR,Sponsored"]),
                    (20, ["AD", "PR", "Sponsored"]),
                )

            def test_parse_args_exclude_trims_whitespace(self):
                self.assertEqual(parse_args(["-x", " AD , PR "]), (20, ["AD", "PR"]))

            def test_parse_args_exclude_drops_empty(self):
                self.assertEqual(parse_args(["-x", "AD,, ,PR,"]), (20, ["AD", "PR"]))

            def test_parse_args_exclude_empty_string(self):
                self.assertEqual(parse_args(["-x", ""]), (20, []))

            def test_parse_args_f_ignored(self):
                # -f는 인자를 받지만 동작에 영향 없음(기본값 유지)
                self.assertEqual(parse_args(["-f", "."]), (20, []))

            def test_parse_args_combined(self):
                self.assertEqual(
                    parse_args(["-f", ".", "-n", "3", "-x", "AD, PR"]),
                    (3, ["AD", "PR"]),
                )

            # --- strip_tags ---

            def test_strip_tags_removes_tags(self):
                self.assertEqual(strip_tags("<h2 class='x'>Hello</h2>"), "Hello")

            def test_strip_tags_strips_whitespace(self):
                self.assertEqual(strip_tags("   <b>Hi</b>   "), "Hi")

            def test_strip_tags_plain_text(self):
                self.assertEqual(strip_tags("  plain  "), "plain")

            def test_strip_tags_empty_after_strip(self):
                self.assertEqual(strip_tags("   <br/>   "), "")

            # --- parse_feed_list ---

            def test_parse_feed_list_basic(self):
                lines = card("/blog/@u/1/", ["Title One"], ["Body text"])
                self.assertEqual(
                    parse_feed_list(lines),
                    [Feed("https://wikidocs.net/blog/@u/1/", "Title One", "Body text")],
                )

            def test_parse_feed_list_skips_whitespace_before_title(self):
                lines = card("/blog/@u/1/", ["   ", "", "Real Title"], ["Body"])
                self.assertEqual(parse_feed_list(lines)[0].title, "Real Title")

            def test_parse_feed_list_joins_multiline_body(self):
                lines = card("/blog/@u/1/", ["Title"], ["   ", "line A", "", "line B"])
                self.assertEqual(parse_feed_list(lines)[0].body, "line A line B")

            def test_parse_feed_list_multiple_cards(self):
                lines = card("/blog/@u/1/", ["T1"], ["B1"]) + card(
                    "/blog/@u/2/", ["T2"], ["B2"]
                )
                feeds = parse_feed_list(lines)
                self.assertEqual(
                    [(f.title, f.body) for f in feeds], [("T1", "B1"), ("T2", "B2")]
                )

            def test_parse_feed_list_dedup_by_link(self):
                lines = card("/blog/@u/1/", ["First"], ["B1"]) + card(
                    "/blog/@u/1/", ["Dup"], ["B2"]
                )
                feeds = parse_feed_list(lines)
                self.assertEqual(len(feeds), 1)
                self.assertEqual(feeds[0].title, "First")

            def test_parse_feed_list_card_without_body(self):
                # break-words 단락이 없는 카드도 다음 카드/끝에서 finalize되어야 한다
                lines = ['<a href="/blog/@u/1/" class="block">']
                lines.append(
                    '<h2 class="text-xl font-bold text-gray-800">No Body Title</h2>'
                )
                lines += card("/blog/@u/2/", ["Has Body"], ["B2"])
                feeds = parse_feed_list(lines)
                self.assertEqual(
                    [(f.title, f.body) for f in feeds],
                    [("No Body Title", ""), ("Has Body", "B2")],
                )

            def test_parse_feed_list_same_line_body(self):
                lines = [
                    '<a href="/blog/@u/1/" class="block">',
                    '<h2 class="text-xl font-bold">Title</h2>',
                    '<p class="break-words">Inline body</p>',
                ]
                self.assertEqual(parse_feed_list(lines)[0].body, "Inline body")

            def test_parse_feed_list_ignores_content_before_anchor(self):
                lines = ["<div>garbage</div>", "<span>noise</span>"] + card(
                    "/blog/@u/1/", ["Title"], ["Body"]
                )
                feeds = parse_feed_list(lines)
                self.assertEqual(len(feeds), 1)
                self.assertEqual(feeds[0].title, "Title")

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), [])

            # --- filter_excluded ---

            def _feeds(self):
                return [
                    Feed("l1", "증시 브리핑", "시장 상태 양호"),
                    Feed("l2", "주택담보대출 금리", "은행 비교"),
                    Feed("l3", "일반 글", "서킷브레이커 발동"),
                ]

            def test_filter_excluded_empty_keywords_returns_all(self):
                feeds = self._feeds()
                self.assertEqual(filter_excluded(feeds, []), feeds)

            def test_filter_excluded_by_title(self):
                result = filter_excluded(self._feeds(), ["증시"])
                self.assertEqual([f.link for f in result], ["l2", "l3"])

            def test_filter_excluded_by_body(self):
                # 제목에는 없고 본문에만 있는 키워드도 제거 대상
                result = filter_excluded(self._feeds(), ["서킷브레이커"])
                self.assertEqual([f.link for f in result], ["l1", "l2"])

            def test_filter_excluded_multiple_keywords(self):
                result = filter_excluded(self._feeds(), ["증시", "주택담보대출"])
                self.assertEqual([f.link for f in result], ["l3"])

            def test_filter_excluded_no_match_keeps_all(self):
                feeds = self._feeds()
                self.assertEqual(filter_excluded(feeds, ["없는키워드"]), feeds)

            def test_filter_excluded_substring(self):
                result = filter_excluded(self._feeds(), ["담보"])
                self.assertEqual([f.link for f in result], ["l1", "l3"])

            # --- print_feeds ---

            def _capture_print(self, feeds, limit):
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    print_feeds(feeds, limit)
                return buf.getvalue()

            def test_print_feeds_format(self):
                output = self._capture_print([Feed("l1", "T1", "B1")], 20)
                self.assertEqual(output, "l1\tT1\n")

            def test_print_feeds_respects_limit(self):
                feeds = [Feed(f"l{i}", f"T{i}", "") for i in range(5)]
                output = self._capture_print(feeds, 2)
                self.assertEqual(output, "l0\tT0\nl1\tT1\n")

            def test_print_feeds_empty(self):
                self.assertEqual(self._capture_print([], 20), "")

        sys.exit(unittest.main())
    else:
        sys.exit(main())
