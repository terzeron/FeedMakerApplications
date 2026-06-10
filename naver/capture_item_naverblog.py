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

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 blog.naver.com PostTitleListAsync(blogId=jeunkim) 응답에서
            #       파서가 읽는 "blogId" 및 "logNo"/"title" 쌍 3개만 한 줄로 샘플링(title은 URL-encoded).
            # 기대 출력: 동일 입력을 'capture_item_naverblog.py'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINE = (
                '{"blogId":"jeunkim","logNo":"224311458992","title":"CWS+%EC%A3%BC%EA%B0%84+%EB%AF%B8%EA%B5%AD+%EC%8B%9C%EC%9E%A5+%EB%A6%AC%EB%B7%B0+-+%EC%82%AC%EC%83%81+%EC%B5%9C%EA%B3%A0%EC%B9%98+%EA%B8%B0%EB%A1%9D+%ED%9B%84+%EB%B0%98%EB%8F%84%EC%B2%B4+%EA%B4%80%EB%A0%A8%EC%A3%BC+%ED%8F%AD%EB%9D%BD%EA%B3%BC+%EA%B2%BD%EC%A0%9C+%EC%A7%80%ED%91%9C+%ED%98%B8%EC%A1%B0+%EC%86%8D+%EB%B3%80%EB%8F%99%EC%84%B1+%EC%A7%80%EC%86%8D",'
                '"logNo":"224310327930","title":"%5B%EC%98%A4%EB%8A%98%EC%9D%98+%EC%B0%A8%ED%8A%B8%5D++%EB%A7%88%EB%B2%A8%2C+S%26P+500+%EC%A7%80%EC%88%98+%ED%8E%B8%EC%9E%85%2C+%EA%B3%BC%EA%B1%B0+%EC%82%AC%EB%A1%80%EB%A5%BC+%EB%B3%B4%EB%A9%B4+%EC%B4%88%EA%B8%B0+%EC%83%81%EC%8A%B9%EC%84%B8%EC%97%90%EB%8A%94+%ED%81%B0+%ED%95%A8%EC%A0%95%EC%9D%B4",'
                '"logNo":"224310851014","title":"%EC%B1%97%EB%B4%87%EB%93%A4%EC%9D%B4+%EC%98%88%EC%B8%A1%ED%95%9C+2026+%EC%9B%94%EB%93%9C%EC%BB%B5+%EC%9A%B0%EC%8A%B9%ED%8C%80%3A+%EC%8A%A4%ED%8E%98%EC%9D%B8+vs+%ED%94%84%EB%9E%91%EC%8A%A4%EC%9D%98+%EC%B9%98%EC%97%B4%ED%95%9C+%EA%B2%BD%EC%9F%81",}'
            )

            def test_real_sample_end_to_end(self):
                result_list, url_prefix = parse_feed_list([self.REAL_SAMPLE_LINE])
                lines = render_lines(result_list, url_prefix, 5)
                self.assertEqual(
                    lines,
                    [
                        "http://blog.naver.com/PostView.naver?blogId=jeunkim&logNo=224311458992\tCWS 주간 미국 시장 리뷰 - 사상 최고치 기록 후 반도체 관련주 폭락과 경제 지표 호조 속 변동성 지속",
                        "http://blog.naver.com/PostView.naver?blogId=jeunkim&logNo=224310327930\t[오늘의 차트]  마벨, S&P 500 지수 편입, 과거 사례를 보면 초기 상승세에는 큰 함정이",
                        "http://blog.naver.com/PostView.naver?blogId=jeunkim&logNo=224310851014\t챗봇들이 예측한 2026 월드컵 우승팀: 스페인 vs 프랑스의 치열한 경쟁",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
