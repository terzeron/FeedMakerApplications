#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple

from bin.feed_maker_util import IO
from bin.crawler import Crawler
from utils.translation import Translation


def parse_args(argv: List[str]) -> Tuple[int, bool]:
    """명령행 인자를 파싱해 (num_of_recent_feeds, debug)를 반환."""
    num_of_recent_feeds = 1000
    debug = False
    optlist, _ = getopt.getopt(argv, "f:n:d")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-d":
            debug = True
    return num_of_recent_feeds, debug


def is_issue_title(line: str) -> bool:
    """'Month Year' 형식의 이슈 제목 줄인지 판별."""
    return bool(re.search(r"^\s*([A-Za-z]+\s+\d{4})\s*(?:</span>)?$", line))


def extract_article_links(html: str) -> List[Tuple[str, str]]:
    """이슈 페이지 HTML에서 cacm article 링크와 제목을 중복 없이 추출."""
    matches = re.findall(
        r'<a href="(https://cacm\.acm\.org/(?:opinion|news|practice|research|blogcacm)/[^"]+/)">([^<]+)</a>',
        html,
    )
    result_list: List[Tuple[str, str]] = []
    seen_links = set()
    for match in matches:
        link = match[0]
        title = match[1].strip()
        if title and link not in seen_links:
            seen_links.add(link)
            result_list.append((link, title))
    return result_list


def main() -> int:
    num_of_recent_feeds, debug = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    issue_links_set = set()
    crawler = Crawler(render_js=True, timeout=60)

    current_link = None
    for line in line_list:
        # communication_archive.html:
        # <a class="archive-issue-timeline-issues-item" href="https://cacm.acm.org/issue/january-2026/">
        # <figure>...</figure>
        # <span class="archive-issue-timeline-issues-item-title">
        # January 2026
        m = re.search(
            r'<a class="archive-issue-timeline-issues-item" href="([^"]+)">', line
        )
        if m:
            current_link = m.group(1)
            continue

        if current_link:
            # title이 있는 줄 찾기 (탭/공백으로 시작, Month Year 형식)
            if is_issue_title(line):
                issue_link = current_link
                if issue_link not in issue_links_set:
                    issue_links_set.add(issue_link)

                    html, error, _ = crawler.run(issue_link)

                    if debug and html:
                        issue_name = issue_link.rstrip("/").split("/")[-1]
                        with open(f"debug_cacm_{issue_name}.html", "w") as f:
                            f.write(html)

                    if html and not error:
                        result_list.extend(extract_article_links(html))
                current_link = None

    translation = Translation()
    result_list = translation.translate(result_list[:num_of_recent_feeds])

    for link, title in result_list[:num_of_recent_feeds]:
        print(f"{link}\t{title}")

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_defaults(self):
                self.assertEqual(parse_args([]), (1000, False))

            def test_parse_args_num_and_debug(self):
                self.assertEqual(parse_args(["-n", "5", "-d"]), (5, True))

            # --- is_issue_title ---

            def test_is_issue_title_match(self):
                self.assertTrue(is_issue_title("   January 2026"))

            def test_is_issue_title_with_span(self):
                self.assertTrue(is_issue_title("  March 2025</span>"))

            def test_is_issue_title_no_match(self):
                self.assertFalse(is_issue_title("<div>not a title</div>"))

            # --- extract_article_links ---

            def test_extract_article_links_basic(self):
                html = '<a href="https://cacm.acm.org/news/abc/">News Title</a>'
                self.assertEqual(
                    extract_article_links(html),
                    [("https://cacm.acm.org/news/abc/", "News Title")],
                )

            def test_extract_article_links_dedups(self):
                html = (
                    '<a href="https://cacm.acm.org/news/abc/">First</a>'
                    '<a href="https://cacm.acm.org/news/abc/">Dup</a>'
                )
                self.assertEqual(len(extract_article_links(html)), 1)

            def test_extract_article_links_multiple_sections(self):
                html = (
                    '<a href="https://cacm.acm.org/opinion/x/">Op</a>'
                    '<a href="https://cacm.acm.org/research/y/">Re</a>'
                )
                self.assertEqual(
                    [t for _, t in extract_article_links(html)], ["Op", "Re"]
                )

            def test_extract_article_links_ignores_other_links(self):
                html = '<a href="https://example.com/foo/">Other</a>'
                self.assertEqual(extract_article_links(html), [])

            def test_extract_article_links_empty(self):
                self.assertEqual(extract_article_links(""), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
