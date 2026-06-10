#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


META_OG_URL_TAG_PATTERN = (
    r'<meta property="og:url" content="(?P<url_prefix>https?://[^/"]+).*"'
)


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 2000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def parse_feed_list(html: List[str]) -> List[Tuple[str, str]]:
    """티스토리 스킨별로 다른 6가지 목록 패턴을 차례대로 적용해 (link, title) 목록을 누적한다."""
    result_list: List[Tuple[str, str]] = []
    link = ""

    # pattern 1: link_post anchor + tit_post strong
    url_prefix = ""
    state = 0
    for line in html:
        if state == 0:
            m = re.search(META_OG_URL_TAG_PATTERN, line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(
                r'<a href="(?P<article_id>/\d+)(?:\?category=\d+)?" class="link_post">',
                line,
            )
            if m:
                link = url_prefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(r'<strong class="tit_post\s*">(?P<title>.+)</strong>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    # pattern 2: <h2><a href="/n">title</a></h2>
    url_prefix = ""
    state = 0
    for line in html:
        if state == 0:
            m = re.search(META_OG_URL_TAG_PATTERN, line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(
                r'<h2><a href="(?P<article_id>/\d+)">(?P<title>.*?)</a></h2>', line
            )
            if m:
                link = url_prefix + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))

    # pattern 3: <h2 class="title"><a href="n">title</a>
    url_prefix = ""
    state = 0
    for line in html:
        if state == 0:
            m = re.search(META_OG_URL_TAG_PATTERN, line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(
                r'<h2 class="title"><a href="(?P<article_id>\d+)">(?P<title>.*)</a>',
                line,
            )
            if m:
                link = url_prefix + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))

    # pattern 4: anchor + span.title
    url_prefix = ""
    state = 0
    for line in html:
        if state == 0:
            m = re.search(META_OG_URL_TAG_PATTERN, line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<article_id>/\d+)(?:\?category=\d+)?">', line)
            if m:
                link = url_prefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(r'<span class="title">(?P<title>.*?)</span>', line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    # pattern 5: <li><a> + tit_blog strong
    url_prefix = ""
    state = 0
    for line in html:
        if state == 0:
            m = re.search(META_OG_URL_TAG_PATTERN, line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(
                r'<li><a href="(?P<article_id>[^"\?]+)(?:\?category=\d+)?">', line
            )
            if m:
                link = url_prefix + m.group("article_id")
                state = 2
        elif state == 2:
            m = re.search(
                r'<strong class="tit_blog"[^>]*>(?P<title>.*?)</strong>', line
            )
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1

    # pattern 6: body.list 영역의 /entry anchor (body.entry에서 종료)
    url_prefix = ""
    state = 0
    for line in html:
        if state == 0:
            m = re.search(META_OG_URL_TAG_PATTERN, line)
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r'<div id="body" class="list">', line)
            if m:
                state = 2
        elif state == 2:
            m = re.search(r'<div id="body" class="entry">', line)
            if m:
                break
            m = re.search(
                r'<a href="(?P<article_id>/entry/[^"?=]+)(?:\?category=\d+)?">(?P<title>.+)</a>',
                line,
            )
            if m:
                link = url_prefix + m.group("article_id")
                title = m.group("title")
                result_list.append((link, title))
                state = 2

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

    html = IO.read_stdin_as_line_list()
    result_list = parse_feed_list(html)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemTistory(unittest.TestCase):
            META = '<meta property="og:url" content="https://blog.test/path">'

            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 2000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- parse_feed_list (각 스킨 패턴) ---

            def test_parse_feed_list_pattern1_link_post(self):
                html = [
                    self.META,
                    '<a href="/42" class="link_post">',
                    '<strong class="tit_post">Post 42</strong>',
                ]
                self.assertEqual(
                    parse_feed_list(html), [("https://blog.test/42", "Post 42")]
                )

            def test_parse_feed_list_pattern2_h2_anchor(self):
                html = [self.META, '<h2><a href="/7">Title 7</a></h2>']
                self.assertEqual(
                    parse_feed_list(html), [("https://blog.test/7", "Title 7")]
                )

            def test_parse_feed_list_pattern6_entry(self):
                html = [
                    self.META,
                    '<div id="body" class="list">',
                    '<a href="/entry/hello-world">Hello World</a>',
                    '<div id="body" class="entry">',
                    '<a href="/entry/should-not-appear">Nope</a>',
                ]
                self.assertEqual(
                    parse_feed_list(html),
                    [("https://blog.test/entry/hello-world", "Hello World")],
                )

            def test_parse_feed_list_no_match(self):
                self.assertEqual(parse_feed_list([self.META, "<div>nothing</div>"]), [])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 2000), ["l1\tA", "l2\tB"]
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://nasica1.tistory.com/?page=1 을 받아온 실제 HTML 중
            #       파서가 매칭하는 영역(og:url + anchor + span.title 블록 3개, pattern 4)만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_tistory.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '<meta property="og:url" content="https://nasica1.tistory.com"/>',
                '\t\t\t\t<a href="/991">',
                '\t\t\t\t\t<span class="title">하나우 전투 (3) - 브레더의 사연</span>',
                '\t\t\t\t<a href="/990">',
                '\t\t\t\t\t<span class="title">남티롤(S&uuml;dtirol) 이야기 (3) - &quot;훼손된 승리&quot;</span>',
                '\t\t\t\t<a href="/989">',
                '\t\t\t\t\t<span class="title">하나우 전투 (2) - 투자와 전쟁에서 예측은 금물</span>',
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_LINES)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://nasica1.tistory.com/991\t하나우 전투 (3) - 브레더의 사연",
                        "https://nasica1.tistory.com/990\t남티롤(S&uuml;dtirol) 이야기 (3) - &quot;훼손된 승리&quot;",
                        "https://nasica1.tistory.com/989\t하나우 전투 (2) - 투자와 전쟁에서 예측은 금물",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
