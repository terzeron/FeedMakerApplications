#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO

# sbxh(뉴토끼 계열) 목록 페이지는 og:url/canonical이 죽은 미러(sbxh6 등,
# 텔레그램 주소 채널로 redirect)를 가리키므로 url prefix로 쓸 수 없다.
# 실제 접속 가능한 도메인을 기본값으로 두고 -u 로 override 한다.
DEFAULT_URL_PREFIX = "https://sbxh9.com"

# Next.js SSR HTML은 한 줄이 매우 길어 line 단위 상태머신 대신 전체 blob에
# 정규식을 적용한다. class="ep-row-v2-link" anchor 안의 href와, 그 뒤
# ep-row-v2-title > strong 텍스트를 (link, title)로 짝짓는다.
# 사이트가 anchor 속성 순서를 바꾸고(href가 class 앞) data-ntk-soft-link
# 같은 속성을 추가해도 깨지지 않도록, class 존재는 lookahead로 확인하고
# href는 태그 내 위치와 무관하게 뽑는다.
_ITEM_PATTERN = re.compile(
    r'<a\b(?=[^>]*\bclass="ep-row-v2-link")[^>]*\bhref="(?P<link>/webtoon/\d+/[^"]+)"[^>]*>'
    r'.*?<div class="ep-row-v2-title"><strong>(?P<title>.*?)</strong>',
    re.DOTALL,
)


def parse_args(argv: List[str]) -> Tuple[int, str]:
    """명령행 인자를 파싱해 (최근 피드 개수, url prefix)를 반환."""
    num_of_recent_feeds = 1000
    url_prefix = DEFAULT_URL_PREFIX
    optlist, _ = getopt.getopt(argv, "f:n:u:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-u":
            url_prefix = a.rstrip("/")
    return num_of_recent_feeds, url_prefix


def parse_feed_list(content: str, url_prefix: str) -> List[Tuple[str, str]]:
    """전체 HTML에서 ep-row-v2-link/ep-row-v2-title를 짝지어 (link, title) 목록을 만든다."""
    result_list: List[Tuple[str, str]] = []
    for m in _ITEM_PATTERN.finditer(content):
        link = url_prefix + m.group("link")
        link = re.sub(r"&amp;", "&", link)
        title = m.group("title")
        title = re.sub(r"&nbsp;", " ", title)
        title = re.sub(r"\s+", " ", title).strip()
        result_list.append((link, title))
    return result_list


def render_lines(result_list: List[Tuple[str, str]], num_of_recent_feeds: int) -> List[str]:
    """전체 개수에서 역순 번호를 매겨 'link\\t%03d. title' 라인 목록을 만든다."""
    num = len(result_list)
    lines: List[str] = []
    for link, title in result_list[:num_of_recent_feeds]:
        lines.append("%s\t%03d. %s" % (link, num, title))
        num -= 1
    return lines


def main() -> int:
    num_of_recent_feeds, url_prefix = parse_args(sys.argv[1:])

    content = "\n".join(IO.read_stdin_as_line_list())
    result_list = parse_feed_list(content, url_prefix)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemSbxh(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), (1000, DEFAULT_URL_PREFIX))

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), (5, DEFAULT_URL_PREFIX))

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "feed.xml"]), (1000, DEFAULT_URL_PREFIX))

            def test_parse_args_url_prefix_override(self):
                self.assertEqual(parse_args(["-u", "https://sbxh10.com/"]), (1000, "https://sbxh10.com"))

            def test_parse_args_combined(self):
                self.assertEqual(parse_args(["-f", ".", "-n", "3"]), (3, DEFAULT_URL_PREFIX))

            # --- parse_feed_list ---

            def _item(self, link, title):
                return f'<a class="ep-row-v2-link" href="{link}"><div class="ep-row-v2-thumb"><img src="x"/><span class="ep-row-v2-no">1</span></div><div class="ep-row-v2-body"><div class="ep-row-v2-title"><strong>{title}</strong></div></div></a>'

            def test_parse_feed_list_basic(self):
                content = self._item("/webtoon/57369982/1237502", "1년차 만렙 매니저 97화")
                self.assertEqual(parse_feed_list(content, DEFAULT_URL_PREFIX), [("https://sbxh9.com/webtoon/57369982/1237502", "1년차 만렙 매니저 97화")])

            def test_parse_feed_list_nonnumeric_epid(self):
                content = self._item("/webtoon/57369982/kp-57369982-69705723", "1년차 만렙 매니저 196화")
                self.assertEqual(parse_feed_list(content, DEFAULT_URL_PREFIX), [("https://sbxh9.com/webtoon/57369982/kp-57369982-69705723", "1년차 만렙 매니저 196화")])

            def test_parse_feed_list_multiple_preserves_order(self):
                content = self._item("/webtoon/1/196", "196화") + self._item("/webtoon/1/195", "195화")
                self.assertEqual(parse_feed_list(content, "https://sbxh9.com"), [("https://sbxh9.com/webtoon/1/196", "196화"), ("https://sbxh9.com/webtoon/1/195", "195화")])

            def test_parse_feed_list_collapses_title_whitespace(self):
                content = self._item("/webtoon/1/1", "  0097 -  1년차   만렙&nbsp;매니저 97화 ")
                self.assertEqual(parse_feed_list(content, "https://sbxh9.com"), [("https://sbxh9.com/webtoon/1/1", "0097 - 1년차 만렙 매니저 97화")])

            def test_parse_feed_list_href_before_class(self):
                # 실제 사이트 마크업: href가 class 앞에 오고 data-ntk-soft-link 속성이 붙는다.
                content = '<a href="/webtoon/59771249/1591484" class="ep-row-v2-link" data-ntk-soft-link=""><div class="ep-row-v2-thumb"><span class="ep-row-v2-no">136</span></div><div class="ep-row-v2-body"><div class="ep-row-v2-title"><strong>사신표월 시즌3 41화(시즌3 마지막화)</strong></div></div></a>'
                self.assertEqual(parse_feed_list(content, DEFAULT_URL_PREFIX), [("https://sbxh9.com/webtoon/59771249/1591484", "사신표월 시즌3 41화(시즌3 마지막화)")])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list("", DEFAULT_URL_PREFIX), [])

            # --- render_lines ---

            def test_render_lines_numbering_descends_from_total(self):
                result = [("l1", "A"), ("l2", "B"), ("l3", "C")]
                self.assertEqual(render_lines(result, 1000), ["l1\t003. A", "l2\t002. B", "l3\t001. C"])

            def test_render_lines_limit_keeps_total_based_numbering(self):
                result = [("l1", "A"), ("l2", "B"), ("l3", "C")]
                self.assertEqual(render_lines(result, 2), ["l1\t003. A", "l2\t002. B"])

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
