#!/usr/bin/env python


import os
import sys
import re
import getopt
import urllib.parse
from typing import List, Tuple

from bin.feed_maker_util import IO


BASE_URL_PREFIX = "http://blog.naver.com/PostView.naver?blogId="


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def clean_title(raw: str) -> str:
    """URL 인코딩과 HTML 엔티티를 풀어 제목을 정규화한다."""
    title = urllib.parse.unquote(raw)
    title = re.sub(r"\+", " ", title)
    title = re.sub(r"&quot;", "'", title)
    title = re.sub(r"&(lt|gt);", "", title)
    title = re.sub(r"\n", " ", title)
    return title


def parse_feed_list(
    line_list: List[str], url_prefix: str = BASE_URL_PREFIX
) -> Tuple[List[Tuple[str, str]], str]:
    """blogId로 url_prefix를 누적하면서 logNo/title을 모아 ((logNo, title) 목록, 최종 url_prefix)를 반환."""
    # 원본 동작 보존: blogId가 여러 번 나오면 url_prefix가 누적되고, 마지막 값이 모든 항목에 쓰인다.
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        m = re.search(r'"blogId"\s*:\s*"(?P<blogId>[^"]+)"', line)
        if m:
            url_prefix = url_prefix + m.group("blogId") + "&logNo="

        for match in re.findall(r'"logNo":"(\d+)","title":"([^"]+)",', line):
            log_no = match[0]
            title = clean_title(match[1])
            result_list.append((log_no, title))
    return result_list, url_prefix


def render_lines(
    result_list: List[Tuple[str, str]], url_prefix: str, num_of_recent_feeds: int
) -> List[str]:
    """(logNo, title) 목록을 'url_prefix+logNo\\ttitle' 라인 목록으로 변환."""
    return [
        "%s\t%s" % (url_prefix + link, title)
        for (link, title) in result_list[:num_of_recent_feeds]
    ]


def main():
    num_of_recent_feeds = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()
    result_list, url_prefix = parse_feed_list(line_list)

    for line in render_lines(result_list, url_prefix, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemNaverBlog(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 30)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            # --- clean_title ---

            def test_clean_title_plus_to_space(self):
                self.assertEqual(clean_title("Hello+World"), "Hello World")

            def test_clean_title_url_unquote(self):
                self.assertEqual(clean_title("Another%20Post"), "Another Post")

            def test_clean_title_quot_to_apostrophe(self):
                self.assertEqual(clean_title("it&quot;s"), "it's")

            def test_clean_title_removes_lt_gt(self):
                self.assertEqual(clean_title("a&lt;b&gt;c"), "abc")

            # --- parse_feed_list ---

            def test_parse_feed_list_basic(self):
                lines = [
                    '{"blogId":"myblog"}',
                    '{"logNo":"123","title":"Hello+World",}',
                ]
                result_list, url_prefix = parse_feed_list(lines)
                self.assertEqual(result_list, [("123", "Hello World")])
                self.assertEqual(
                    url_prefix,
                    "http://blog.naver.com/PostView.naver?blogId=myblog&logNo=",
                )

            def test_parse_feed_list_multiple_logno_in_one_line(self):
                lines = ['{"logNo":"1","title":"A","x":1,"logNo":"2","title":"B",}']
                result_list, _ = parse_feed_list(lines)
                self.assertEqual([n for n, _ in result_list], ["1", "2"])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), ([], BASE_URL_PREFIX))

            # --- render_lines ---

            def test_render_lines_prepends_url_prefix(self):
                self.assertEqual(
                    render_lines([("123", "T")], "http://p/?logNo=", 30),
                    ["http://p/?logNo=123\tT"],
                )

            def test_render_lines_limit(self):
                result = [("1", "A"), ("2", "B"), ("3", "C")]
                self.assertEqual(render_lines(result, "p", 2), ["p1\tA", "p2\tB"])

        # --- 입력 스키마 골든 마스터 테스트(기존 보존) ---

        class TestNaverBlogSchema(unittest.TestCase):
            SAMPLE_INPUT_FOR_SCHEMA = """var mInfo = {"viewDate":"20240728","blogId":"test_user_123","logNo":"223534275525","title":"Sample Blog Post Title 1","nickName":"Tester"};
var oData = {"logNo":"223534275525","title":"Sample+Blog+Post+Title+1","content":"...","commentCnt":7,"taglist":["tag1","tag2"]};
var anotherData = {"logNo":"223534275526","title":"Another%20Post%20Title","content":"...","commentCnt":10,"taglist":[]};
"""

            GOLDEN_SCHEMA = """var mInfo = {"viewDate":"__DATE__","blogId":"__BLOG_ID__","logNo":"__LOG_NO__","title":"__TITLE__","nickName":"__NICKNAME__"};
var oData = {"logNo":"__LOG_NO__","title":"__TITLE__","content":"...","commentCnt":__NUMBER__,"taglist":__LIST__};
var anotherData = {"logNo":"__LOG_NO__","title":"__TITLE__","content":"...","commentCnt":__NUMBER__,"taglist":__LIST__};
"""

            def _anonymize_line(self, line):
                anonymization_rules = [
                    (r'("blogId"\s*:\s*")([^"]+)(")', r"\1__BLOG_ID__\3"),
                    (r'("logNo"\s*:\s*")([^"]+)(")', r"\1__LOG_NO__\3"),
                    (r'("title"\s*:\s*")([^"]+)(")', r"\1__TITLE__\3"),
                    (r'("viewDate"\s*:\s*")([^"]+)(")', r"\1__DATE__\3"),
                    (r'("nickName"\s*:\s*")([^"]+)(")', r"\1__NICKNAME__\3"),
                    (r'("commentCnt"\s*:\s*)(\d+)', r"\1__NUMBER__"),
                    (r'("taglist"\s*:\s*)(\[.*\])', r"\1__LIST__"),
                ]
                for pattern, replacement in anonymization_rules:
                    line = re.sub(pattern, replacement, line)
                return line

            def test_input_schema_is_unchanged(self):
                input_lines = self.SAMPLE_INPUT_FOR_SCHEMA.strip().splitlines()
                golden_lines = self.GOLDEN_SCHEMA.strip().splitlines()
                anonymized_lines = [self._anonymize_line(line) for line in input_lines]
                self.assertEqual(anonymized_lines, golden_lines)

        sys.exit(unittest.main())
    else:
        sys.exit(main())
