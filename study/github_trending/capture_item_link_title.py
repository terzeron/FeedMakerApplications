#!/usr/bin/env python

"""GitHub Trending과 Git Breakout을 하나의 'link<TAB>title' 목록으로 캡처한다.

두 소스 모두 아이템이 GitHub 저장소 페이지라 한 피드로 합쳤다. conf.json의
list_url_list에 두 URL이 들어 있어 이 스크립트가 수집 때마다 두 번 불린다.
어느 쪽이 들어왔는지는 stdin이 JSON인지로 가른다.

Git Breakout은 timeline에서 최신 스냅샷 id만 얻을 수 있어 ranking API를 한 번 더
부른다. official_ranks가 있는 저장소는 GitHub Trending 쪽에 이미 나오므로 뺀다.

제목은 'owner/repo: 한국어설명(English description)' 형식이다. 저장소 이름은
번역 대상이 아니므로 설명만 번역한다.
"""

import os
import re
import sys
import json
import getopt
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Tuple

from bs4 import BeautifulSoup

from bin.crawler import Crawler, Method
from utils.translation import Translation

GITHUB_BASE = "https://github.com"
GITBREAKOUT_BASE = "https://gitbreakout.imbch.dev"

# official_ranks 필터가 페이지의 절반 가까이를 걷어내므로 넉넉히 받아 온다.
_MIN_PAGE_SIZE = 45
_MAX_PAGE_SIZE = 100

_WHITESPACE_RE = re.compile(r"\s+")


class Options(NamedTuple):
    num_of_recent_feeds: int
    do_translate: bool
    feed_dir_path: Path


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
    feed_dir_path = Path.cwd()

    optlist, _ = getopt.getopt(argv, "f:n:t")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            do_translate = True
        elif o == "-f":
            feed_dir_path = Path(a)

    return Options(num_of_recent_feeds, do_translate, feed_dir_path)


def is_json_input(text: str) -> bool:
    """stdin이 Git Breakout timeline JSON인지 판정한다."""
    return text.lstrip().startswith("{")


def parse_github_trending(markup: str, limit: int = 0) -> List[Tuple[str, str, str]]:
    """GitHub Trending 페이지에서 (url, full_name, description) 목록을 뽑는다."""
    soup = BeautifulSoup(markup, "html.parser")
    result_list: List[Tuple[str, str, str]] = []
    for row in soup.select("article.Box-row"):
        anchor = row.select_one("h2 a")
        if not anchor or not anchor.get("href"):
            continue
        full_name = clean(anchor.get_text(" ", strip=True)).replace(" / ", "/")
        url = GITHUB_BASE + anchor["href"]

        desc_tag = row.select_one("p")
        description = clean(desc_tag.get_text(" ", strip=True)) if desc_tag else ""

        result_list.append((url, full_name, description))
        if limit and len(result_list) >= limit:
            break
    return result_list


def latest_snapshot_id(timeline: Dict[str, Any]) -> str:
    """timeline 응답에서 가장 최근 스냅샷 id를 꺼낸다."""
    snapshots = timeline.get("snapshots") or []
    if not snapshots:
        return ""
    return str(snapshots[-1].get("id", ""))


def ranking_page_size(limit: int) -> int:
    """official_ranks 필터로 줄어들 양을 감안한 page_size를 정한다."""
    if not limit:
        return _MAX_PAGE_SIZE
    return min(_MAX_PAGE_SIZE, max(3 * limit, _MIN_PAGE_SIZE))


def parse_gitbreakout_ranking(
    payload: Dict[str, Any], limit: int = 0
) -> List[Tuple[str, str, str]]:
    """ranking 응답에서 (url, full_name, description) 목록을 뽑는다.

    GitHub이 이미 순위에 올린 저장소(official_ranks에 값이 있음)는 뺀다.
    """
    result_list: List[Tuple[str, str, str]] = []
    for repo in payload.get("repositories") or []:
        full_name = repo.get("full_name")
        url = repo.get("url")
        if not full_name or not url:
            continue
        if any((repo.get("official_ranks") or {}).values()):
            continue

        result_list.append(
            (str(url), str(full_name), clean(repo.get("description") or ""))
        )
        if limit and len(result_list) >= limit:
            break
    return result_list


def fetch_gitbreakout_ranking(
    timeline_json: str, limit: int, feed_dir_path: Path
) -> List[Tuple[str, str, str]]:
    """timeline JSON을 받아 ranking API를 한 번 더 부르고 목록으로 만든다."""
    snapshot_id = latest_snapshot_id(json.loads(timeline_json))
    if not snapshot_id:
        return []

    url = (
        f"{GITBREAKOUT_BASE}/api/ranking?snapshot={snapshot_id}"
        f"&page=1&page_size={ranking_page_size(limit)}&view=momentum"
    )
    crawler = Crawler(
        dir_path=feed_dir_path,
        method=Method.GET,
        headers={"Accept": "application/json"},
    )
    result, error, _ = crawler.run(url)
    if not result:
        print(f"Error: can't get ranking from '{url}', {error}", file=sys.stderr)
        return []
    return parse_gitbreakout_ranking(json.loads(result), limit=limit)


def compose_repo_title(full_name: str, description: str, translated: str) -> str:
    """저장소 제목을 'owner/repo: 설명' 형식으로 만든다.

    저장소 이름은 번역 대상이 아니므로 그대로 두고 설명만 바꿔 끼운다.
    설명이 없으면 저장소 이름만 남는다.
    """
    if not description:
        return full_name
    return f"{full_name}: {translated or description}"


def build_titles(
    repo_list: List[Tuple[str, str, str]], do_translate: bool
) -> List[Tuple[str, str]]:
    """(url, full_name, description) 목록을 (link, title) 목록으로 만든다."""
    translated_map: Dict[str, str] = {}
    if do_translate:
        translated_map = translate_texts([desc for _, _, desc in repo_list])

    return [
        (url, compose_repo_title(full_name, desc, translated_map.get(desc, "")))
        for url, full_name, desc in repo_list
    ]


def main() -> int:
    opts = parse_args(sys.argv[1:])
    input_data = sys.stdin.read()

    if is_json_input(input_data):
        repo_list = fetch_gitbreakout_ranking(
            input_data, opts.num_of_recent_feeds, opts.feed_dir_path
        )
    else:
        repo_list = parse_github_trending(input_data, limit=opts.num_of_recent_feeds)

    for line in render_lines(build_titles(repo_list, opts.do_translate)):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_defaults(self):
                opts = parse_args([])
                self.assertEqual((opts.num_of_recent_feeds, opts.do_translate), (20, False))

            def test_parse_args_combined(self):
                opts = parse_args(["-t", "-n", "5", "-f", "/tmp/feed"])
                self.assertEqual(opts.num_of_recent_feeds, 5)
                self.assertTrue(opts.do_translate)
                self.assertEqual(opts.feed_dir_path, Path("/tmp/feed"))

            # --- clean / render_lines / is_translation_failed ---

            def test_clean_collapses_whitespace(self):
                self.assertEqual(clean("  a \n  b  "), "a b")

            def test_clean_handles_none(self):
                self.assertEqual(clean(None), "")

            def test_is_translation_failed_true(self):
                self.assertTrue(is_translation_failed("Hello", "Hello(Hello)"))

            def test_is_translation_failed_false(self):
                self.assertFalse(is_translation_failed("Hello", "안녕(Hello)"))

            def test_render_lines_uses_tab(self):
                self.assertEqual(
                    render_lines([("http://a.test/1", "a/one: first repo")]),
                    ["http://a.test/1\ta/one: first repo"],
                )

            def test_render_lines_drops_empty(self):
                self.assertEqual(render_lines([("", "t"), ("http://a.test/1", "")]), [])

            # --- is_json_input ---

            def test_is_json_input_true(self):
                self.assertTrue(is_json_input('\n  {"snapshots": []}'))

            def test_is_json_input_false_for_html(self):
                self.assertFalse(is_json_input("<!DOCTYPE html>\n<html>"))

            # --- parse_github_trending ---

            GITHUB_SAMPLE = """
            <article class="Box-row">
              <h2><a href="/ayghri/i-have-adhd"> ayghri / i-have-adhd </a></h2>
              <p>  A task manager
                   for ADHD brains  </p>
            </article>
            <article class="Box-row">
              <h2><a href="/foo/bar">foo / bar</a></h2>
            </article>
            """

            def test_parse_github_trending_basic(self):
                self.assertEqual(
                    parse_github_trending(self.GITHUB_SAMPLE)[0],
                    (
                        "https://github.com/ayghri/i-have-adhd",
                        "ayghri/i-have-adhd",
                        "A task manager for ADHD brains",
                    ),
                )

            def test_parse_github_trending_without_description(self):
                self.assertEqual(
                    parse_github_trending(self.GITHUB_SAMPLE)[1],
                    ("https://github.com/foo/bar", "foo/bar", ""),
                )

            def test_parse_github_trending_limit(self):
                self.assertEqual(len(parse_github_trending(self.GITHUB_SAMPLE, limit=1)), 1)

            def test_parse_github_trending_empty(self):
                self.assertEqual(parse_github_trending("<html></html>"), [])

            # --- latest_snapshot_id ---

            def test_latest_snapshot_id_takes_last(self):
                timeline = {"snapshots": [{"id": "old"}, {"id": "new"}]}
                self.assertEqual(latest_snapshot_id(timeline), "new")

            def test_latest_snapshot_id_empty(self):
                self.assertEqual(latest_snapshot_id({"snapshots": []}), "")

            def test_latest_snapshot_id_missing_key(self):
                self.assertEqual(latest_snapshot_id({}), "")

            # --- ranking_page_size ---

            def test_ranking_page_size_no_limit(self):
                self.assertEqual(ranking_page_size(0), 100)

            def test_ranking_page_size_small_limit_uses_floor(self):
                self.assertEqual(ranking_page_size(5), 45)

            def test_ranking_page_size_triples(self):
                self.assertEqual(ranking_page_size(20), 60)

            def test_ranking_page_size_caps(self):
                self.assertEqual(ranking_page_size(300), 100)

            # --- parse_gitbreakout_ranking ---

            RANKING_SAMPLE = {
                "repositories": [
                    {
                        "full_name": "a/one",
                        "url": "https://github.com/a/one",
                        "description": "first  repo",
                        "official_ranks": {"daily": None, "weekly": None},
                    },
                    {
                        "full_name": "b/two",
                        "url": "https://github.com/b/two",
                        "description": "already trending",
                        "official_ranks": {"daily": 3},
                    },
                    {"full_name": "c/three", "url": None},
                ]
            }

            def test_parse_gitbreakout_ranking_keeps_unranked(self):
                self.assertEqual(
                    parse_gitbreakout_ranking(self.RANKING_SAMPLE),
                    [("https://github.com/a/one", "a/one", "first repo")],
                )

            def test_parse_gitbreakout_ranking_empty_payload(self):
                self.assertEqual(parse_gitbreakout_ranking({}), [])

            # --- compose_repo_title / build_titles ---

            def test_compose_repo_title_prefers_translation(self):
                self.assertEqual(
                    compose_repo_title("a/one", "first repo", "첫 저장소(first repo)"),
                    "a/one: 첫 저장소(first repo)",
                )

            def test_compose_repo_title_without_description(self):
                self.assertEqual(compose_repo_title("a/one", "", ""), "a/one")

            def test_build_titles_without_translation(self):
                repo_list = [("https://github.com/a/one", "a/one", "first repo")]
                self.assertEqual(
                    build_titles(repo_list, False),
                    [("https://github.com/a/one", "a/one: first repo")],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
