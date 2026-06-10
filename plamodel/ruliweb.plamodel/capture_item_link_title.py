#!/usr/bin/env python


import os
import sys
import re
import getopt
import json
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urljoin, urlparse
from bin.feed_maker_util import IO


KEYWORD_EXCLUSION_LIST = [
    "가면라이더",
    "헥사기어",
    "Warhammer",
    "워해머",
    "아수라",
    "키즈나",
    "메가미",
    "카나메",
    "반간",
    "다간",
    "리베르 나이트",
    "창채소녀",
    "판타지 포레스트",
    "리벨 나이트",
    "루나마리아",
    "FRS",
    "젠레스",
    "니콜 데마라",
    "아니메스타",
    "30MS",
    "30ms",
    "츠키루나",
    "드라몬",
    "판타지스타",
    "30MF",
    "30mf",
    "베앗가이",
    "하츠네미쿠",
    "PLAMATEA",
    "유피아",
    "플라맥스",
    "미유키",
    "애니메스터",
    "제네 티어즈",
    "아르카나디아",
    "소피에라",
    "피겨라이즈",
    "미오리네",
    "램블랑",
    "블렛 엑소시스트",
    "시스루",
    "푸니모푸",
    "프레이아",
    "모데로이드",
    "프레임암즈",
    "하츠네 미쿠",
    "사이버 포뮬러",
    "사이버포뮬러",
    "SMP SRX",
    "말딸",
]


def extract_base_url(html_lines: list) -> str | None:
    for line in html_lines:
        m = re.search(r'<meta property="og:url" content="(?P<og_url>[^"]+)">', line)
        if m:
            return m.group("og_url")
    return None


def parse_args(argv: List[str]) -> Tuple[Path, int]:
    """명령행 인자를 파싱해 (feed_dir_path, num_of_recent_feeds)를 반환."""
    feed_dir_path = Path.cwd()
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-f":
            feed_dir_path = Path(a)
    return feed_dir_path, num_of_recent_feeds


def parse_feed_list(
    line_list: List[str],
    link_prefix: str,
    keyword_exclusion_list: List[str] = KEYWORD_EXCLUSION_LIST,
) -> List[Tuple[str, str]]:
    """subject 셀 → subject_link 링크 → 제목 순으로 훑되, 제외 키워드가 포함된 제목은 건너뛴다."""
    state = 0
    link = ""
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<td class="subject">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(
                r'<a class="subject_link deco" href="(?P<link>[^\?"]+)[^"]*">', line
            )
            if m:
                link = m.group("link")
                link = re.sub(r"&amp;", "&", link)
                link = urljoin(link_prefix, link)
                state = 2
        elif state == 2:
            m = re.search(
                r"^\s{3,}(?:<strong>)?\s*(?P<title>\S[^<>]+\S)\s*(?:</strong>)?\s{3,}",
                line,
            )
            if m:
                title = m.group("title")
                state = 3
                for keyword in keyword_exclusion_list:
                    if keyword in title:
                        state = 0
                        break
                if state != 0:
                    result_list.append((link, title))
                    state = 0
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """(link, title) 목록을 'link\\ttitle' 라인 목록으로 변환."""
    return [
        "%s\t%s" % (link, title) for (link, title) in result_list[:num_of_recent_feeds]
    ]


def main():
    feed_dir_path, num_of_recent_feeds = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()

    link_prefix = extract_base_url(line_list)
    if link_prefix is None:
        # Fallback to conf.json if base URL not found in HTML
        conf_file_path = feed_dir_path / "conf.json"
        with open(conf_file_path, "r", encoding="utf-8") as f:
            conf = json.load(f)
        first_list_url = conf["configuration"]["collection"]["list_url_list"][0]
        parsed_url = urlparse(first_list_url)
        link_prefix = f"{parsed_url.scheme}://{parsed_url.netloc}"

    result_list = parse_feed_list(line_list, link_prefix)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemLinkTitle(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default_num(self):
                self.assertEqual(parse_args([])[1], 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"])[1], 5)

            def test_parse_args_feed_dir(self):
                self.assertEqual(parse_args(["-f", "/tmp/x"])[0], Path("/tmp/x"))

            # --- extract_base_url ---

            def test_extract_base_url_found(self):
                lines = ['<meta property="og:url" content="https://ruli.test/board">']
                self.assertEqual(extract_base_url(lines), "https://ruli.test/board")

            def test_extract_base_url_not_found(self):
                self.assertIsNone(extract_base_url(["<div>nope</div>"]))

            # --- parse_feed_list ---

            def _entry(self, link, title):
                return [
                    '<td class="subject">',
                    f'<a class="subject_link deco" href="{link}">',
                    f"      {title}      ",
                ]

            def test_parse_feed_list_basic(self):
                lines = self._entry("/board/read/100", "Cool Model")
                self.assertEqual(
                    parse_feed_list(lines, "https://ruli.test"),
                    [("https://ruli.test/board/read/100", "Cool Model")],
                )

            def test_parse_feed_list_strips_query_in_link(self):
                lines = self._entry("/board/read/100?page=2", "Model")
                self.assertEqual(
                    parse_feed_list(lines, "https://ruli.test")[0][0],
                    "https://ruli.test/board/read/100",
                )

            def test_parse_feed_list_excludes_keyword(self):
                lines = self._entry("/r/1", "가면라이더 키트")
                self.assertEqual(parse_feed_list(lines, "https://ruli.test"), [])

            def test_parse_feed_list_custom_keyword_list(self):
                lines = self._entry("/r/1", "Banned Item")
                self.assertEqual(
                    parse_feed_list(lines, "https://ruli.test", ["Banned"]), []
                )

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([], "https://ruli.test"), [])

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

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://bbs.ruliweb.com/family/232/board/300077 을 받아온 실제 HTML 중
            #       파서가 매칭하는 (td.subject → subject_link → 제목) 블록 3개만 샘플링(og:url은 없음).
            # 기대 출력: link_prefix를 conf의 list_url 도메인(https://bbs.ruliweb.com)으로 주고
            #          parse_feed_list → render_lines로 만든 결과(= a.py 직접 실행과 동일).
            REAL_SAMPLE_LINES = [
                '                            <td class="subject">',
                '                                <a class="subject_link deco" href="https://bbs.ruliweb.com/family/232/board/300077/read/23060243?">',
                '                     allkyung님의 육군 K311 자작 (1/6)                    <i class="icon-picture"></i>                                                            <span class="num_reply" data-href="https://bbs.ruliweb.com/family/232/board/300077/read/23060243?#cmt" target="_self"> (18)</span>                                    </a>',
                '        <td class="subject">',
                '                                <a class="subject_link deco" href="https://bbs.ruliweb.com/family/232/board/300077/read/22885741?">',
                '                    (HS.Kim[우찬아빠]님 작품)최고의 전함 &quot;미주리&quot;...                    <i class="icon-picture"></i>                                                            <span class="num_reply" data-href="https://bbs.ruliweb.com/family/232/board/300077/read/22885741?#cmt" target="_self"> (11)</span>                                    </a>',
                '        <td class="subject">',
                '                                <a class="subject_link deco" href="https://bbs.ruliweb.com/family/232/board/300077/read/14528341?">',
                '                    오아시스[oasis]님의 제천대성(1/6 레진)                    <i class="icon-picture"></i>                                                            <span class="num_reply" data-href="https://bbs.ruliweb.com/family/232/board/300077/read/14528341?#cmt" target="_self"> (6)</span>                                    </a>',
            ]

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(
                    self.REAL_SAMPLE_LINES, "https://bbs.ruliweb.com"
                )
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://bbs.ruliweb.com/family/232/board/300077/read/23060243\tallkyung님의 육군 K311 자작 (1/6)",
                        "https://bbs.ruliweb.com/family/232/board/300077/read/22885741\t(HS.Kim[우찬아빠]님 작품)최고의 전함 &quot;미주리&quot;...",
                        "https://bbs.ruliweb.com/family/232/board/300077/read/14528341\t오아시스[oasis]님의 제천대성(1/6 레진)",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
