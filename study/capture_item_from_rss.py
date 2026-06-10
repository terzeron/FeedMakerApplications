#!/usr/bin/env python


import os
import sys
import getopt
from typing import Iterable, List, NamedTuple, Tuple
from urllib.parse import urlsplit, urlunsplit

from utils.translation import Translation

import feedparser


class Options(NamedTuple):
    num_of_recent_feeds: int
    do_translate: bool
    do_strip_query: bool
    exclusion_keywords: List[str]


def _strip_query(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def parse_exclusion_keywords(arg: str) -> List[str]:
    """콤마로 구분된 제외키워드 문자열을 공백 제거 후 빈 항목을 뺀 리스트로 변환."""
    return [k.strip() for k in arg.split(",") if k.strip()]


def parse_args(argv: List[str]) -> Options:
    """명령행 인자를 파싱해 Options로 반환."""
    num_of_recent_feeds = 1000
    do_translate = False
    do_strip_query = False
    exclusion_keywords: List[str] = []

    optlist, _ = getopt.getopt(argv, "f:n:tsx:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            do_translate = True
        elif o == "-s":
            do_strip_query = True
        elif o == "-x":
            exclusion_keywords = parse_exclusion_keywords(a)

    return Options(
        num_of_recent_feeds, do_translate, do_strip_query, exclusion_keywords
    )


def normalize_entry(entry: dict, do_strip_query: bool) -> Tuple[str, str]:
    """RSS entry 하나에서 (link, title)을 정규화해 추출."""
    title = " ".join((entry.get("title", "") or "").split())
    link = (entry.get("link", "") or "").strip()
    if do_strip_query:
        link = _strip_query(link)
    return link, title


def is_excluded(title: str, exclusion_keywords: List[str]) -> bool:
    """title에 제외키워드가 하나라도 포함되면 True."""
    return any(keyword in title for keyword in exclusion_keywords)


def collect_items(
    entries: Iterable[dict], do_strip_query: bool, exclusion_keywords: List[str]
) -> List[Tuple[str, str]]:
    """entry 목록에서 link/title을 정규화하고, 빈 값·중복·제외키워드 항목을 걸러 (link, title) 리스트를 만든다."""
    result_list: List[Tuple[str, str]] = []
    seen: set[str] = set()
    for entry in entries:
        link, title = normalize_entry(entry, do_strip_query)
        if not link or not title or link in seen:
            continue
        if is_excluded(title, exclusion_keywords):
            continue
        seen.add(link)
        result_list.append((link, title))
    return result_list


def translate_items(result_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """제목을 번역한 (link, title) 리스트로 반환."""
    return Translation().translate(result_list)


def format_line(link: str, title: str) -> str:
    """출력 한 줄(link\\ttitle)을 만든다. 번역 결과의 공백도 정규화한다."""
    title = " ".join(title.split())
    return f"{link}\t{title}"


def render_lines(result_list: List[Tuple[str, str]]) -> List[str]:
    """(link, title) 리스트를 출력 라인 리스트로 변환."""
    return [format_line(link, title) for link, title in result_list]


def main() -> int:
    opts = parse_args(sys.argv[1:])

    feed = feedparser.parse(sys.stdin.read())
    result_list = collect_items(
        feed.entries, opts.do_strip_query, opts.exclusion_keywords
    )
    result_list = result_list[: opts.num_of_recent_feeds]

    if opts.do_translate:
        result_list = translate_items(result_list)

    for line in render_lines(result_list):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest
        from unittest.mock import MagicMock, patch

        class TestCaptureItemFromRss(unittest.TestCase):
            # --- _strip_query ---

            def test_strip_query_removes_query(self):
                self.assertEqual(
                    _strip_query("http://a.test/p?x=1&y=2"), "http://a.test/p"
                )

            def test_strip_query_removes_fragment(self):
                self.assertEqual(_strip_query("http://a.test/p#sec"), "http://a.test/p")

            def test_strip_query_removes_query_and_fragment(self):
                self.assertEqual(
                    _strip_query("http://a.test/p?x=1#sec"), "http://a.test/p"
                )

            def test_strip_query_keeps_clean_url(self):
                self.assertEqual(_strip_query("http://a.test/p"), "http://a.test/p")

            def test_strip_query_no_path(self):
                self.assertEqual(_strip_query("http://a.test?x=1"), "http://a.test")

            # --- parse_exclusion_keywords ---

            def test_parse_exclusion_keywords_single(self):
                self.assertEqual(parse_exclusion_keywords("AD"), ["AD"])

            def test_parse_exclusion_keywords_multiple(self):
                self.assertEqual(
                    parse_exclusion_keywords("AD,Sponsored,PR"),
                    ["AD", "Sponsored", "PR"],
                )

            def test_parse_exclusion_keywords_trims_whitespace(self):
                self.assertEqual(
                    parse_exclusion_keywords(" AD , Sponsored "), ["AD", "Sponsored"]
                )

            def test_parse_exclusion_keywords_drops_empty(self):
                self.assertEqual(
                    parse_exclusion_keywords("AD,,Sponsored,"), ["AD", "Sponsored"]
                )

            def test_parse_exclusion_keywords_empty_string(self):
                self.assertEqual(parse_exclusion_keywords(""), [])

            def test_parse_exclusion_keywords_only_commas(self):
                self.assertEqual(parse_exclusion_keywords(",, ,"), [])

            # --- parse_args ---

            def test_parse_args_defaults(self):
                opts = parse_args([])
                self.assertEqual(opts, Options(1000, False, False, []))

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]).num_of_recent_feeds, 5)

            def test_parse_args_translate(self):
                self.assertTrue(parse_args(["-t"]).do_translate)

            def test_parse_args_strip_query(self):
                self.assertTrue(parse_args(["-s"]).do_strip_query)

            def test_parse_args_exclusion(self):
                self.assertEqual(
                    parse_args(["-x", "AD, PR"]).exclusion_keywords, ["AD", "PR"]
                )

            def test_parse_args_f_ignored(self):
                # -f는 인자를 받지만 동작에 영향 없음(기본값 유지)
                self.assertEqual(
                    parse_args(["-f", "feed.xml"]), Options(1000, False, False, [])
                )

            def test_parse_args_combined(self):
                opts = parse_args(["-n", "3", "-t", "-s", "-x", "AD,PR"])
                self.assertEqual(opts, Options(3, True, True, ["AD", "PR"]))

            # --- normalize_entry ---

            def test_normalize_entry_basic(self):
                self.assertEqual(
                    normalize_entry(
                        {"title": "Hello", "link": "http://a.test/1"}, False
                    ),
                    ("http://a.test/1", "Hello"),
                )

            def test_normalize_entry_collapses_title_whitespace(self):
                self.assertEqual(
                    normalize_entry(
                        {"title": "Hello   World\n", "link": "http://a.test/1"}, False
                    ),
                    ("http://a.test/1", "Hello World"),
                )

            def test_normalize_entry_strips_link_whitespace(self):
                self.assertEqual(
                    normalize_entry(
                        {"title": "T", "link": "  http://a.test/1  "}, False
                    ),
                    ("http://a.test/1", "T"),
                )

            def test_normalize_entry_strip_query(self):
                self.assertEqual(
                    normalize_entry(
                        {"title": "T", "link": "http://a.test/1?x=1"}, True
                    ),
                    ("http://a.test/1", "T"),
                )

            def test_normalize_entry_no_strip_query(self):
                self.assertEqual(
                    normalize_entry(
                        {"title": "T", "link": "http://a.test/1?x=1"}, False
                    ),
                    ("http://a.test/1?x=1", "T"),
                )

            def test_normalize_entry_missing_fields(self):
                self.assertEqual(normalize_entry({}, False), ("", ""))

            def test_normalize_entry_none_values(self):
                self.assertEqual(
                    normalize_entry({"title": None, "link": None}, False), ("", "")
                )

            # --- is_excluded ---

            def test_is_excluded_match(self):
                self.assertTrue(is_excluded("Buy AD now", ["AD"]))

            def test_is_excluded_no_match(self):
                self.assertFalse(is_excluded("Hello World", ["AD"]))

            def test_is_excluded_empty_keywords(self):
                self.assertFalse(is_excluded("anything", []))

            def test_is_excluded_substring(self):
                self.assertTrue(is_excluded("Sponsored content", ["Sponsor"]))

            def test_is_excluded_multiple_keywords_second_matches(self):
                self.assertTrue(is_excluded("PR release", ["AD", "PR"]))

            # --- collect_items ---

            def test_collect_items_basic(self):
                entries = [
                    {"title": "A", "link": "http://a.test/1"},
                    {"title": "B", "link": "http://a.test/2"},
                ]
                self.assertEqual(
                    collect_items(entries, False, []),
                    [("http://a.test/1", "A"), ("http://a.test/2", "B")],
                )

            def test_collect_items_dedup_by_link(self):
                entries = [
                    {"title": "A", "link": "http://a.test/1"},
                    {"title": "A dup", "link": "http://a.test/1"},
                ]
                self.assertEqual(
                    collect_items(entries, False, []), [("http://a.test/1", "A")]
                )

            def test_collect_items_dedup_after_strip_query(self):
                entries = [
                    {"title": "A", "link": "http://a.test/1?x=1"},
                    {"title": "A2", "link": "http://a.test/1?y=2"},
                ]
                self.assertEqual(
                    collect_items(entries, True, []), [("http://a.test/1", "A")]
                )

            def test_collect_items_skips_missing_link(self):
                entries = [
                    {"title": "A", "link": ""},
                    {"title": "B", "link": "http://a.test/2"},
                ]
                self.assertEqual(
                    collect_items(entries, False, []), [("http://a.test/2", "B")]
                )

            def test_collect_items_skips_missing_title(self):
                entries = [
                    {"title": "", "link": "http://a.test/1"},
                    {"title": "B", "link": "http://a.test/2"},
                ]
                self.assertEqual(
                    collect_items(entries, False, []), [("http://a.test/2", "B")]
                )

            def test_collect_items_excludes_keyword(self):
                entries = [
                    {"title": "Hello", "link": "http://a.test/1"},
                    {"title": "Buy AD", "link": "http://a.test/2"},
                    {"title": "Sponsored", "link": "http://a.test/3"},
                ]
                self.assertEqual(
                    collect_items(entries, False, ["AD", "Sponsored"]),
                    [("http://a.test/1", "Hello")],
                )

            def test_collect_items_preserves_order(self):
                entries = [
                    {"title": "C", "link": "http://a.test/3"},
                    {"title": "A", "link": "http://a.test/1"},
                    {"title": "B", "link": "http://a.test/2"},
                ]
                self.assertEqual(
                    [t for _, t in collect_items(entries, False, [])], ["C", "A", "B"]
                )

            def test_collect_items_empty(self):
                self.assertEqual(collect_items([], False, []), [])

            # --- translate_items ---

            def test_translate_items_delegates_to_translation(self):
                mock_translation = MagicMock()
                mock_translation.translate.return_value = [("http://a.test/1", "안녕")]
                with patch("__main__.Translation", return_value=mock_translation):
                    result = translate_items([("http://a.test/1", "Hello")])
                self.assertEqual(result, [("http://a.test/1", "안녕")])
                mock_translation.translate.assert_called_once_with(
                    [("http://a.test/1", "Hello")]
                )

            # --- format_line ---

            def test_format_line_basic(self):
                self.assertEqual(
                    format_line("http://a.test/1", "Hello"), "http://a.test/1\tHello"
                )

            def test_format_line_collapses_whitespace(self):
                self.assertEqual(
                    format_line("http://a.test/1", "Hello   World\n"),
                    "http://a.test/1\tHello World",
                )

            # --- render_lines ---

            def test_render_lines_multiple(self):
                result = render_lines(
                    [("http://a.test/1", "A"), ("http://a.test/2", "B")]
                )
                self.assertEqual(result, ["http://a.test/1\tA", "http://a.test/2\tB"])

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([]), [])

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://www.brendangregg.com/blog/rss.xml 을 받아온 실제 RSS의
            #       feedparser entry 중 (link, title) 3개만 샘플링한 것.
            # 기대 출력: 번역(-t) 없이 동일 입력을 'capture_item_from_rss.py'로 실행해 캡처한 결과.
            REAL_SAMPLE_ENTRIES = [
                {
                    "link": "http://www.brendangregg.com/blog//2026-02-07/why-i-joined-openai.html",
                    "title": "Why I joined OpenAI",
                },
                {
                    "link": "http://www.brendangregg.com/blog//2025-12-05/leaving-intel.html",
                    "title": "Leaving Intel",
                },
                {
                    "link": "http://www.brendangregg.com/blog//2025-11-28/ai-virtual-brendans.html",
                    "title": 'On "AI Brendans" or "Virtual Brendans"',
                },
            ]

            def test_real_sample_end_to_end(self):
                result = collect_items(self.REAL_SAMPLE_ENTRIES, False, [])
                lines = render_lines(result)
                self.assertEqual(
                    lines,
                    [
                        "http://www.brendangregg.com/blog//2026-02-07/why-i-joined-openai.html\tWhy I joined OpenAI",
                        "http://www.brendangregg.com/blog//2025-12-05/leaving-intel.html\tLeaving Intel",
                        'http://www.brendangregg.com/blog//2025-11-28/ai-virtual-brendans.html\tOn "AI Brendans" or "Virtual Brendans"',
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
