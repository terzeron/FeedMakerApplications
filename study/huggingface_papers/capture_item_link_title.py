#!/usr/bin/env python

"""Hugging Face 트렌딩 논문 목록을 'link<TAB>title'로 캡처한다.

논문 카드는 <article> 안의 /papers/ 링크로 식별한다. 같은 논문이 여러 카드에
걸쳐 나올 수 있어 경로 기준으로 한 번만 담는다. 제목은 번역하고 본문은 두지 않는다.
"""

import os
import re
import sys
import getopt
from typing import Dict, List, NamedTuple, Tuple

from bs4 import BeautifulSoup

from utils.translation import Translation

HUGGINGFACE_BASE = "https://huggingface.co"

_PAPER_PATH_RE = re.compile(r"^/papers/\S")
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
    num_of_recent_feeds = 20
    do_translate = False

    optlist, _ = getopt.getopt(argv, "f:n:t")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            do_translate = True

    return Options(num_of_recent_feeds, do_translate)


def parse_papers(markup: str, limit: int = 0) -> List[Tuple[str, str]]:
    """트렌딩 페이지에서 (link, 영문 제목) 목록을 뽑는다."""
    soup = BeautifulSoup(markup, "html.parser")
    result_list: List[Tuple[str, str]] = []
    seen: set = set()

    for article in soup.select("article"):
        anchor = article.select_one('a[href^="/papers/"]')
        if not anchor or not anchor.get("href"):
            continue
        href = anchor["href"]
        if not _PAPER_PATH_RE.match(href) or href in seen:
            continue
        seen.add(href)

        heading = article.find(["h3", "h4", "h2"])
        source = heading if heading else anchor
        title = clean(source.get_text(" ", strip=True))
        if not title:
            continue

        result_list.append((HUGGINGFACE_BASE + href, title))
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

    result_list = parse_papers(sys.stdin.read(), limit=opts.num_of_recent_feeds)
    for line in render_lines(apply_translation(result_list, opts.do_translate)):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemLinkTitle(unittest.TestCase):
            SAMPLE = """
            <article>
              <a href="/papers/2412.20138"></a>
              <h3>  TradingAgents:
                    Multi-Agents LLM Framework </h3>
            </article>
            <article>
              <a href="/papers/2412.20138"></a>
              <h3>중복 카드</h3>
            </article>
            <article>
              <a href="/papers/2503.08638">YuE: Long-Form Music Generation</a>
            </article>
            <article><a href="/papers/">목록 링크</a></article>
            """

            # --- parse_args ---

            def test_parse_args_defaults(self):
                self.assertEqual(parse_args([]), Options(20, False))

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

            # --- parse_papers ---

            def test_parse_papers_uses_heading(self):
                self.assertEqual(
                    parse_papers(self.SAMPLE)[0],
                    (
                        "https://huggingface.co/papers/2412.20138",
                        "TradingAgents: Multi-Agents LLM Framework",
                    ),
                )

            def test_parse_papers_skips_duplicate_href(self):
                links = [link for link, _ in parse_papers(self.SAMPLE)]
                self.assertEqual(len(links), len(set(links)))

            def test_parse_papers_falls_back_to_anchor_text(self):
                self.assertEqual(
                    parse_papers(self.SAMPLE)[1],
                    (
                        "https://huggingface.co/papers/2503.08638",
                        "YuE: Long-Form Music Generation",
                    ),
                )

            def test_parse_papers_skips_index_link(self):
                self.assertEqual(len(parse_papers(self.SAMPLE)), 2)

            def test_parse_papers_limit(self):
                self.assertEqual(len(parse_papers(self.SAMPLE, limit=1)), 1)

            def test_parse_papers_empty(self):
                self.assertEqual(parse_papers("<html></html>"), [])

            # --- apply_translation ---

            def test_apply_translation_disabled_is_identity(self):
                result_list = [("http://a.test/1", "Title")]
                self.assertEqual(apply_translation(result_list, False), result_list)

        sys.exit(unittest.main())
    else:
        sys.exit(main())
