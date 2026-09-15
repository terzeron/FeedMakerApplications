#!/usr/bin/env python

"""Star History 블로그 목록을 'link<TAB>title'로 캡처한다.

목록에는 날짜 없는 안내 글(고정 글)이 섞여 있다. 그 글은 트렌드 신호가 아니므로
발행일이 붙은 카드만 담는다. 제목은 번역하고 본문은 두지 않는다.
"""

import os
import re
import sys
import getopt
from typing import Dict, List, NamedTuple, Tuple

from bs4 import BeautifulSoup

from utils.translation import Translation

STAR_HISTORY_BASE = "https://www.star-history.com"

# 'Sep 5, 2026' 형태의 발행일
_DATE_RE = re.compile(r"^[A-Z][a-z]{2}\s+\d{1,2},\s+\d{4}$")
_WHITESPACE_RE = re.compile(r"\s+")


class Options(NamedTuple):
    num_of_recent_feeds: int
    do_translate: bool


def clean(text: str) -> str:
    """연속 공백을 하나로 줄이고 앞뒤 공백을 없앤다."""
    return _WHITESPACE_RE.sub(" ", text or "").strip()


def is_translation_failed(original: str, translated: str) -> bool:
    """'ko(en)' 결과에서 ko와 en이 같으면 번역이 안 된 것으로 본다."""
    return translated == f"{original}({original})"


def translate_texts(text_list: List[str]) -> Dict[str, str]:
    """영문 텍스트를 '한국어(English)'로 옮긴 {원문: 번역} 맵을 만든다.

    번역에 실패한 항목은 캐시에 남지 않으므로 한 번만 다시 시도한다.
    """
    unique = [text for text in dict.fromkeys(text_list) if text]
    if not unique:
        return {}

    translation = Translation()
    result = dict(translation.translate([(text, text) for text in unique]))

    failed = [
        (text, text)
        for text in unique
        if is_translation_failed(text, result.get(text, ""))
    ]
    if failed:
        result.update(dict(translation.translate(failed)))
    return result


def render_lines(result_list: List[Tuple[str, str]]) -> List[str]:
    """(link, title) 목록을 'link\\ttitle' 라인 목록으로 만든다."""
    return [
        f"{link}\t{clean(title)}" for link, title in result_list if link and title
    ]


def parse_args(argv: List[str]) -> Options:
    """명령행 인자를 파싱해 Options로 반환."""
    num_of_recent_feeds = 10
    do_translate = False

    optlist, _ = getopt.getopt(argv, "f:n:t")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            do_translate = True

    return Options(num_of_recent_feeds, do_translate)


def find_published_date(anchor) -> str:
    """카드 안의 <span> 중 발행일 형태인 것을 찾는다. 없으면 빈 문자열."""
    for span in anchor.find_all("span"):
        text = clean(span.get_text(" ", strip=True))
        if _DATE_RE.match(text):
            return text
    return ""


def parse_posts(markup: str, limit: int = 0) -> List[Tuple[str, str]]:
    """블로그 목록에서 (link, 영문 제목) 목록을 뽑는다."""
    soup = BeautifulSoup(markup, "html.parser")
    result_list: List[Tuple[str, str]] = []
    seen: set = set()

    for anchor in soup.select('a[href^="/blog/"]'):
        href = anchor.get("href")
        heading = anchor.find(["h2", "h3"])
        if not href or not heading or href in seen:
            continue
        if not find_published_date(anchor):
            continue
        seen.add(href)

        title = clean(heading.get_text(" ", strip=True))
        if not title:
            continue

        result_list.append((STAR_HISTORY_BASE + href, title))
        if limit and len(result_list) >= limit:
            break
    return result_list


def apply_translation(
    result_list: List[Tuple[str, str]], do_translate: bool
) -> List[Tuple[str, str]]:
    """제목만 '한국어(English)'로 바꾼 목록을 만든다."""
    if not do_translate:
        return result_list
    translated_map = translate_texts([title for _, title in result_list])
    return [(link, translated_map.get(title, title)) for link, title in result_list]


def main() -> int:
    opts = parse_args(sys.argv[1:])

    result_list = parse_posts(sys.stdin.read(), limit=opts.num_of_recent_feeds)
    for line in render_lines(apply_translation(result_list, opts.do_translate)):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemLinkTitle(unittest.TestCase):
            SAMPLE = """
            <a href="/blog/new-github-star-history-api">
              <h2>The New GitHub  Star History API</h2>
              <span>Sep 5, 2026</span>
            </a>
            <a href="/blog/add-a-live-star-history-chart">
              <h2>How to add a chart</h2>
              <span>Guide</span>
            </a>
            <a href="/blog/new-github-star-history-api">
              <h2>중복 카드</h2>
              <span>Sep 5, 2026</span>
            </a>
            <a href="/blog/harness">
              <h2>Star History Monthly August 2026</h2>
              <span>Aug 31, 2026</span>
            </a>
            """

            # --- parse_args ---

            def test_parse_args_defaults(self):
                self.assertEqual(parse_args([]), Options(10, False))

            def test_parse_args_combined(self):
                self.assertEqual(parse_args(["-t", "-n", "3"]), Options(3, True))

            # --- clean / render_lines / is_translation_failed ---

            def test_clean_collapses_whitespace(self):
                self.assertEqual(clean("  a \n  b  "), "a b")

            def test_is_translation_failed_true(self):
                self.assertTrue(is_translation_failed("Hello", "Hello(Hello)"))

            def test_is_translation_failed_false(self):
                self.assertFalse(is_translation_failed("Hello", "안녕(Hello)"))

            def test_render_lines_uses_tab(self):
                self.assertEqual(
                    render_lines([("http://a.test/1", "제목(Title)")]),
                    ["http://a.test/1\t제목(Title)"],
                )

            def test_render_lines_drops_empty(self):
                self.assertEqual(render_lines([("", "t"), ("http://a.test/1", "")]), [])

            # --- find_published_date ---

            def test_find_published_date_match(self):
                anchor = BeautifulSoup(
                    "<a><span>Sep 5, 2026</span></a>", "html.parser"
                ).a
                self.assertEqual(find_published_date(anchor), "Sep 5, 2026")

            def test_find_published_date_no_match(self):
                anchor = BeautifulSoup("<a><span>Guide</span></a>", "html.parser").a
                self.assertEqual(find_published_date(anchor), "")

            # --- parse_posts ---

            def test_parse_posts_collapses_title_whitespace(self):
                self.assertEqual(
                    parse_posts(self.SAMPLE)[0],
                    (
                        "https://www.star-history.com/blog/new-github-star-history-api",
                        "The New GitHub Star History API",
                    ),
                )

            def test_parse_posts_skips_undated_card(self):
                links = [link for link, _ in parse_posts(self.SAMPLE)]
                self.assertNotIn(
                    "https://www.star-history.com/blog/add-a-live-star-history-chart",
                    links,
                )

            def test_parse_posts_skips_duplicate_href(self):
                self.assertEqual(len(parse_posts(self.SAMPLE)), 2)

            def test_parse_posts_limit(self):
                self.assertEqual(len(parse_posts(self.SAMPLE, limit=1)), 1)

            def test_parse_posts_empty(self):
                self.assertEqual(parse_posts("<html></html>"), [])

            # --- apply_translation ---

            def test_apply_translation_disabled_is_identity(self):
                result_list = [("http://a.test/1", "Title")]
                self.assertEqual(apply_translation(result_list, False), result_list)

        sys.exit(unittest.main())
    else:
        sys.exit(main())
