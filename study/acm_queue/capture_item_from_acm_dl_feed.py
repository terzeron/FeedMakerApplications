#!/usr/bin/env python


import getopt
import html
import os
import re
import sys
from time import struct_time
from typing import Iterable, List, NamedTuple, Tuple

import feedparser
from utils.translation import Translation


QUEUE_DETAIL_URL = "https://queue.acm.org/detail.cfm?ref=rss&id={article_id}"
DOI_ID_PATTERN = re.compile(r"10\.1145/(\d+)")
XML_VIEWER_PATTERN = re.compile(
    r'<div id="webkit-xml-viewer-source-xml">(.*?)</div>', re.DOTALL
)


class Options(NamedTuple):
    num_of_recent_feeds: int
    do_translate: bool


def parse_args(argv: List[str]) -> Options:
    num_of_recent_feeds = 1000
    do_translate = False

    optlist, _ = getopt.getopt(argv, "f:n:t")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            do_translate = True

    return Options(num_of_recent_feeds, do_translate)


def extract_feed_source(input_data: str) -> str:
    """Chromium XML viewer HTML이면 hidden raw XML을 복원하고, 아니면 원문을 그대로 반환."""
    match = XML_VIEWER_PATTERN.search(input_data)
    if not match:
        return input_data
    return html.unescape(match.group(1))


def normalize_title(title: str) -> str:
    return " ".join((title or "").split())


def extract_article_id(entry: dict) -> str:
    for key in ("prism_doi", "dc_identifier", "id", "link"):
        value = entry.get(key, "") or ""
        match = DOI_ID_PATTERN.search(value)
        if match:
            return match.group(1)
    return ""


def entry_sort_key(entry: dict) -> Tuple[int, int, int, int, int, int]:
    parsed = entry.get("updated_parsed")
    if isinstance(parsed, struct_time):
        return parsed[:6]
    return (0, 0, 0, 0, 0, 0)


def collect_items(entries: Iterable[dict]) -> List[Tuple[str, str]]:
    result_list: List[Tuple[str, str]] = []
    seen_links: set[str] = set()

    for entry in sorted(entries, key=entry_sort_key, reverse=True):
        article_id = extract_article_id(entry)
        title = normalize_title(entry.get("title", ""))
        if not article_id or not title:
            continue

        link = QUEUE_DETAIL_URL.format(article_id=article_id)
        if link in seen_links:
            continue
        seen_links.add(link)
        result_list.append((link, title))

    return result_list


def _is_translation_failed(original_title: str, translated_title: str) -> bool:
    return translated_title == f"{original_title}({original_title})"


def translate_items(result_list: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    translation = Translation()
    translated = translation.translate(result_list)
    original_by_link = dict(result_list)

    failed = [
        (link, original_by_link[link])
        for link, title in translated
        if link in original_by_link
        and _is_translation_failed(original_by_link[link], title)
    ]
    if not failed:
        return translated

    retried = dict(translation.translate(failed))
    return [(link, retried.get(link, title)) for link, title in translated]


def render_lines(result_list: List[Tuple[str, str]]) -> List[str]:
    return [f"{link}\t{normalize_title(title)}" for link, title in result_list]


def main() -> int:
    opts = parse_args(sys.argv[1:])
    input_data = extract_feed_source(sys.stdin.read())
    feed = feedparser.parse(input_data)
    result_list = collect_items(feed.entries)
    result_list = result_list[: opts.num_of_recent_feeds]

    if opts.do_translate:
        result_list = translate_items(result_list)

    for line in render_lines(result_list):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import io
        import unittest
        from contextlib import redirect_stdout
        from unittest.mock import patch

        class TestCaptureItemFromAcmDlFeed(unittest.TestCase):
            SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
         xmlns="http://purl.org/rss/1.0/"
         xmlns:dc="http://purl.org/dc/elements/1.1/"
         xmlns:prism="http://prismstandard.org/namespaces/basic/2.0/">
   <channel rdf:about="https://dl.acm.org/loi/queue?af=R">
      <title>Association for Computing Machinery: Queue: Table of Contents</title>
      <items>
         <rdf:Seq>
            <rdf:li rdf:resource="https://dl.acm.org/doi/abs/10.1145/3831358?af=R"/>
         </rdf:Seq>
      </items>
   </channel>
   <item rdf:about="https://dl.acm.org/doi/abs/10.1145/3831358?af=R">
      <title>The Challenge of Efficiency Versus Isolation</title>
      <link>https://dl.acm.org/doi/abs/10.1145/3831358?af=R</link>
      <dc:identifier>doi:10.1145/3831358</dc:identifier>
      <prism:doi>10.1145/3831358</prism:doi>
   </item>
</rdf:RDF>"""

            def test_parse_args_defaults(self):
                self.assertEqual(parse_args([]), Options(1000, False))

            def test_parse_args_num_and_translate(self):
                self.assertEqual(parse_args(["-n", "5", "-t"]), Options(5, True))

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "feed_dir"]), Options(1000, False))

            def test_extract_feed_source_from_xml_viewer_html(self):
                wrapped = (
                    '<div id="webkit-xml-viewer-source-xml">'
                    "&lt;rss&gt;&lt;channel/&gt;&lt;/rss&gt;"
                    "</div>"
                )
                self.assertEqual(
                    extract_feed_source(wrapped), "<rss><channel/></rss>"
                )

            def test_extract_article_id_from_prism_doi(self):
                self.assertEqual(
                    extract_article_id({"prism_doi": "10.1145/3831358"}),
                    "3831358",
                )

            def test_extract_article_id_from_link(self):
                self.assertEqual(
                    extract_article_id(
                        {"link": "https://dl.acm.org/doi/abs/10.1145/3831358?af=R"}
                    ),
                    "3831358",
                )

            def test_collect_items_maps_doi_to_queue_detail_url(self):
                feed = feedparser.parse(self.SAMPLE_FEED)
                self.assertEqual(
                    collect_items(feed.entries),
                    [
                        (
                            "https://queue.acm.org/detail.cfm?ref=rss&id=3831358",
                            "The Challenge of Efficiency Versus Isolation",
                        )
                    ],
                )

            def test_collect_items_deduplicates_by_queue_detail_url(self):
                entries = [
                    {"link": "https://dl.acm.org/doi/abs/10.1145/3831358?af=R", "title": "A"},
                    {"prism_doi": "10.1145/3831358", "title": "B"},
                ]
                self.assertEqual(
                    collect_items(entries),
                    [("https://queue.acm.org/detail.cfm?ref=rss&id=3831358", "A")],
                )

            def test_collect_items_sorts_by_updated_date_descending(self):
                entries = [
                    {
                        "prism_doi": "10.1145/1",
                        "title": "Older",
                        "updated_parsed": struct_time((2026, 8, 1, 0, 0, 0, 0, 0, 0)),
                    },
                    {
                        "prism_doi": "10.1145/2",
                        "title": "Newer",
                        "updated_parsed": struct_time((2026, 8, 2, 0, 0, 0, 0, 0, 0)),
                    },
                ]
                self.assertEqual(
                    collect_items(entries),
                    [
                        ("https://queue.acm.org/detail.cfm?ref=rss&id=2", "Newer"),
                        ("https://queue.acm.org/detail.cfm?ref=rss&id=1", "Older"),
                    ],
                )

            def test_main_outputs_queue_detail_links(self):
                stdin = io.StringIO(self.SAMPLE_FEED)
                stdout = io.StringIO()
                with patch("sys.stdin", stdin), redirect_stdout(stdout):
                    self.assertEqual(main(), 0)
                self.assertEqual(
                    stdout.getvalue().strip(),
                    "https://queue.acm.org/detail.cfm?ref=rss&id=3831358\t"
                    "The Challenge of Efficiency Versus Isolation",
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
