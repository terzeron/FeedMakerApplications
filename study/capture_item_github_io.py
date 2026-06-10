#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


def parse_args(argv: List[str]) -> Tuple[int, List[str]]:
    """명령행 인자를 파싱해 (num_of_recent_feeds, 위치 인자 목록)을 반환."""
    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds, args


def parse_feed_list(line_list: List[str], url_prefix: str) -> List[Tuple[str, str]]:
    """toctree 항목과 chapter 항목(다음 줄에 링크/제목)을 훑어 (link, title) 목록을 만든다."""
    state = 0
    link = ""
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(
                r'<li\s+class="chapter\s*"\s+data-level="[^"]+"\s+data-path="[^"]+">',
                line,
            )
            if m:
                state = 1
            m = re.search(
                r'<li class="toctree-[^"]+"><a[^>]*href="(?P<link>[^"\#]+)">(?P<title>.+)</a>',
                line,
            )
            if m:
                link = url_prefix + m.group("link")
                title = m.group("title")
                result_list.append((link, title))
                state = 0
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)">', line)
            if m:
                link = url_prefix + m.group("link")
                link = re.sub(r" ", "%20", link)
                state = 2
        elif state == 2:
            m = re.search(r"^\s+(?P<title>\S+.*\S+)\s+$", line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 0
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """오름차순 번호를 매겨 'link\\t%03d. title' 라인 목록을 만든다."""
    lines: List[str] = []
    num = 1
    for link, title in result_list[:num_of_recent_feeds]:
        lines.append("%s\t%03d. %s" % (link, num, title))
        num += 1
    return lines


def main():
    num_of_recent_feeds, args = parse_args(sys.argv[1:])
    url_prefix = args[0]

    line_list = IO.read_stdin_as_line_list()
    result_list = parse_feed_list(line_list, url_prefix)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemGithubIo(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default_num(self):
                self.assertEqual(parse_args(["http://p/"])[0], 1000)

            def test_parse_args_num(self):
                self.assertEqual(
                    parse_args(["-n", "5", "http://p/"]), (5, ["http://p/"])
                )

            # --- parse_feed_list ---

            def test_parse_feed_list_toctree_item(self):
                lines = [
                    '<li class="toctree-l1"><a class="x" href="page/1.html">Title One</a>',
                ]
                self.assertEqual(
                    parse_feed_list(lines, "http://p/"),
                    [("http://p/page/1.html", "Title One")],
                )

            def test_parse_feed_list_chapter_item(self):
                lines = [
                    '<li class="chapter " data-level="1.1" data-path="x">',
                    '<a href="ch/1 a.html">',
                    "    Chapter Title    ",
                ]
                result = parse_feed_list(lines, "http://p/")
                # 공백은 %20으로 인코딩된다
                self.assertEqual(result, [("http://p/ch/1%20a.html", "Chapter Title")])

            def test_parse_feed_list_multiple_toctree(self):
                lines = [
                    '<li class="toctree-l1"><a href="a.html">A</a>',
                    '<li class="toctree-l1"><a href="b.html">B</a>',
                ]
                self.assertEqual(
                    [t for _, t in parse_feed_list(lines, "http://p/")], ["A", "B"]
                )

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([], "http://p/"), [])

            # --- render_lines ---

            def test_render_lines_ascending_numbering(self):
                result = [("l1", "A"), ("l2", "B"), ("l3", "C")]
                self.assertEqual(
                    render_lines(result, 1000),
                    ["l1\t001. A", "l2\t002. B", "l3\t003. C"],
                )

            def test_render_lines_limit(self):
                result = [("l1", "A"), ("l2", "B"), ("l3", "C")]
                self.assertEqual(render_lines(result, 2), ["l1\t001. A", "l2\t002. B"])

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://kabbala.github.io/grammatica_latina/index.html 을
            #       받아온 실제 HTML 중 파서가 매칭하는 toctree 항목(# 없는 링크) 3개만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_github_io.py <url_prefix>'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '<li class="toctree-l1"><a class="reference internal" href="prooemium.html">머리말</a></li>',
                '<li class="toctree-l1"><a class="reference internal" href="introductio/divisio.html">라틴어의 분류</a><ul>',
                '<li class="toctree-l1"><a class="reference internal" href="introductio/aliae_linguae.html">라틴어와 다른 언어와의 관계</a><ul>',
            ]

            def test_real_sample_end_to_end(self):
                url_prefix = "https://kabbala.github.io/grammatica_latina/"
                result = parse_feed_list(self.REAL_SAMPLE_LINES, url_prefix)
                lines = render_lines(result, 1000)
                self.assertEqual(
                    lines,
                    [
                        "https://kabbala.github.io/grammatica_latina/prooemium.html\t001. 머리말",
                        "https://kabbala.github.io/grammatica_latina/introductio/divisio.html\t002. 라틴어의 분류",
                        "https://kabbala.github.io/grammatica_latina/introductio/aliae_linguae.html\t003. 라틴어와 다른 언어와의 관계",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
