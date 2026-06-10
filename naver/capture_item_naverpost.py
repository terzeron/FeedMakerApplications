#!/usr/bin/env python

import os
import sys
import re
import getopt
import json
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "http://m.post.naver.com"


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def extract_html(content: str) -> str:
    """stdin 내용(JSON)에서 html 필드를 추출(없으면 빈 문자열)."""
    content = re.sub(r"\\\'", "'", content)
    data = json.loads(content)
    return data.get("html", "")


def clean_title(title: str) -> str:
    """제목의 양끝 공백과 HTML 엔티티를 정리한다."""
    title = re.sub(r"^\s+|\s+$", "", title)
    title = re.sub(r"&#39;", "'", title)
    title = re.sub(r"&#40;", ")", title)
    title = re.sub(r"&#41;", "(", title)
    title = re.sub(r"&lt;", "<", title)
    title = re.sub(r"&gt;", ">", title)
    title = re.sub(r"&nbsp;", " ", title)
    title = re.sub(r"&quot;", '"', title)
    title = re.sub(r"</h3>", "", title)
    return title


def parse_feed_list(html: str, url_prefix: str = URL_PREFIX) -> List[Tuple[str, str]]:
    """html 본문을 상태머신으로 훑어 (link, title) 목록을 만든다."""
    link = ""
    title = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in html.split("\n"):
        if state == 0:
            m = re.search(
                r'<a href="(?P<url>/viewer/postView\.naver\?volumeNo=\d+&memberNo=\d+)"',
                line,
            )
            if m:
                url = m.group("url")
                url = re.sub(r"&lt;", "<", url)
                url = re.sub(r"&gt;", ">", url)
                link = url_prefix + url
                title = ""
                state = 1
        elif state == 1:
            if re.search(r'class="link_end"', line):
                state = 2
            else:
                state = 0
        elif state == 2:
            if re.search(r'<h3 class="tit_feed', line):
                state = 3
            else:
                if re.search(r'<strong class="tit_feed', line):
                    state = 4
                else:
                    state = 0
        elif state == 3:
            m = re.search(r"\s*(?P<title>\S+.*\S+)\s*", line)
            if m:
                title = clean_title(m.group("title"))
                if link and title:
                    result_list.append((link, title))
                state = 0
        elif state == 4:
            m = re.search(
                r'(<i class="[^"]+" aria-label="[^"]+"></i>)?(?P<title>.*)</strong>',
                line,
            )
            if m:
                title = clean_title(m.group("title"))
                if link and title:
                    result_list.append((link, title))
                state = 0
            else:
                line = re.sub(r'<i class="[^"]+" aria-label="[^"]+"></i>', "", line)
                title += line
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

    content = "".join(IO.read_stdin_as_line_list())
    html = extract_html(content)
    result_list = parse_feed_list(html)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemNaverpost(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- extract_html ---

            def test_extract_html_basic(self):
                self.assertEqual(
                    extract_html('{"html": "<div>x</div>"}'), "<div>x</div>"
                )

            def test_extract_html_unescapes_backslash_quote(self):
                # 입력의 \' (잘못된 JSON 이스케이프)를 '로 바꾼 뒤 파싱한다
                self.assertEqual(extract_html('{"html": "it\\\'s ok"}'), "it's ok")

            def test_extract_html_missing_key(self):
                self.assertEqual(extract_html('{"other": 1}'), "")

            # --- clean_title ---

            def test_clean_title_strips_whitespace(self):
                self.assertEqual(clean_title("  hello  "), "hello")

            def test_clean_title_entities(self):
                self.assertEqual(clean_title("a&#39;b&lt;c&gt;d&quot;e"), "a'b<c>d\"e")

            def test_clean_title_removes_h3_close(self):
                self.assertEqual(clean_title("title</h3>"), "title")

            # --- parse_feed_list ---

            def test_parse_feed_list_h3_path(self):
                html = "\n".join(
                    [
                        '<a href="/viewer/postView.naver?volumeNo=1&memberNo=2">',
                        '<div class="link_end">',
                        '<h3 class="tit_feed">',
                        "My Post Title",
                    ]
                )
                self.assertEqual(
                    parse_feed_list(html),
                    [
                        (
                            "http://m.post.naver.com/viewer/postView.naver?volumeNo=1&memberNo=2",
                            "My Post Title",
                        )
                    ],
                )

            def test_parse_feed_list_strong_path(self):
                html = "\n".join(
                    [
                        '<a href="/viewer/postView.naver?volumeNo=3&memberNo=4">',
                        '<span class="link_end">',
                        '<strong class="tit_feed">',
                        "Strong Title</strong>",
                    ]
                )
                self.assertEqual(parse_feed_list(html)[0][1], "Strong Title")

            def test_parse_feed_list_requires_link_end(self):
                # link 다음 줄에 link_end가 없으면 state가 리셋되어 수집되지 않는다
                html = "\n".join(
                    [
                        '<a href="/viewer/postView.naver?volumeNo=1&memberNo=2">',
                        "<div>noise</div>",
                        '<h3 class="tit_feed">',
                        "Title",
                    ]
                )
                self.assertEqual(parse_feed_list(html), [])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list(""), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 1000), ["l1\tA", "l2\tB"]
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
