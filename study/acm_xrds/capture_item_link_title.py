#!/usr/bin/env python


import os
import sys
import re
import getopt
import logging
from typing import List, Tuple

from bin.feed_maker_util import IO
from bin.crawler import Crawler
from utils.translation import Translation

LOGGER = logging.getLogger()


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


def parse_issue_link(line: str) -> str | None:
    """xrds 아카이브 줄에서 이슈 페이지 절대 URL을 추출(없으면 None)."""
    m = re.search(r'<h3><a href="(archives\.cfm\?iid=\d+)">', line)
    if m:
        return "https://xrds.acm.org/" + m.group(1)
    return None


def extract_article_links(html: str) -> List[Tuple[str, str]]:
    """이슈 페이지 HTML에서 article 링크와 제목을 중복 없이 추출."""
    matches = re.findall(
        r'<h3><a href="(article\.cfm\?aid=\d+)">([^<]+)</a></h3>', html
    )
    result_list: List[Tuple[str, str]] = []
    for match in matches:
        link = "https://xrds.acm.org/" + match[0]
        title = match[1].strip()
        if title and (link, title) not in result_list:
            result_list.append((link, title))
    return result_list


def main() -> int:
    num_of_recent_feeds, debug = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()
    result_list: List[Tuple[str, str]] = []
    issue_links_set = set()
    crawler = None
    max_volumes = 2  # 처음 2개 볼륨만 크롤링

    for line in line_list:
        if len(issue_links_set) >= max_volumes:
            break
        # xrds_archive.html: <h3><a href="archives.cfm?iid=3764099">Summer 2025 | Volume 31, No. 4</a></h3>
        issue_link = parse_issue_link(line)
        if issue_link:
            if issue_link not in issue_links_set:
                issue_links_set.add(issue_link)
                LOGGER.debug("Crawling %s", issue_link)

                try:
                    if crawler is None:
                        crawler = Crawler(render_js=True, timeout=60)
                    html, error, _ = crawler.run(issue_link)
                except Exception:
                    crawler = Crawler(render_js=True, timeout=60)
                    html, error, _ = crawler.run(issue_link)

                if debug and html:
                    iid = issue_link.split("=")[1]
                    with open(f"debug_xrds_{iid}.html", "w") as f:
                        f.write(html)
                    LOGGER.debug("Saved to debug_xrds_%s.html", iid)

                if html and not error:
                    articles = extract_article_links(html)
                    for link, title in articles:
                        if (link, title) not in result_list:
                            result_list.append((link, title))
                    LOGGER.debug("Found %d articles", len(articles))
                else:
                    LOGGER.error("Crawler error: %s", error)

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
                self.assertEqual(parse_args(["-n", "3", "-d"]), (3, True))

            # --- parse_issue_link ---

            def test_parse_issue_link_basic(self):
                line = '<h3><a href="archives.cfm?iid=3764099">Summer 2025</a></h3>'
                self.assertEqual(
                    parse_issue_link(line),
                    "https://xrds.acm.org/archives.cfm?iid=3764099",
                )

            def test_parse_issue_link_no_match(self):
                self.assertIsNone(parse_issue_link("<div>nope</div>"))

            # --- extract_article_links ---

            def test_extract_article_links_basic(self):
                html = '<h3><a href="article.cfm?aid=123">My Article</a></h3>'
                self.assertEqual(
                    extract_article_links(html),
                    [("https://xrds.acm.org/article.cfm?aid=123", "My Article")],
                )

            def test_extract_article_links_dedups(self):
                html = (
                    '<h3><a href="article.cfm?aid=1">Same</a></h3>'
                    '<h3><a href="article.cfm?aid=1">Same</a></h3>'
                )
                self.assertEqual(len(extract_article_links(html)), 1)

            def test_extract_article_links_multiple(self):
                html = (
                    '<h3><a href="article.cfm?aid=1">A</a></h3>'
                    '<h3><a href="article.cfm?aid=2">B</a></h3>'
                )
                self.assertEqual(
                    [t for _, t in extract_article_links(html)], ["A", "B"]
                )

            def test_extract_article_links_strips_title(self):
                html = '<h3><a href="article.cfm?aid=1">  Spaced  </a></h3>'
                self.assertEqual(extract_article_links(html)[0][1], "Spaced")

            def test_extract_article_links_empty(self):
                self.assertEqual(extract_article_links(""), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
