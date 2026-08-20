#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List, Tuple
from bin.feed_maker_util import IO


URL_PREFIX = "https://terms.naver.com"

# 2026 사이트 리뉴얼 이후 목록 페이지는 <a> 태그가 아니라 Next.js flight 데이터
# (역슬래시로 이스케이프된 JSON 문자열)로 항목을 내려준다. 레코드 하나는
# ...\"publicId\":\"...\",...,\"title\":\"...\",...,\"url\":\"/카테고리/슬러그-id\"... 형태다.
ITEM_PATTERN = re.compile(
    r'\\"publicId\\":\\"[^\\]+\\".*?\\"title\\":\\"(?P<title>[^\\]+)\\".*?\\"url\\":\\"(?P<url>[^\\]+)\\"',
    re.DOTALL,
)


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def parse_feed_list(
    content: str, url_prefix: str = URL_PREFIX
) -> List[Tuple[str, str]]:
    """지식백과 페이지(카테고리 무관)에 내장된 flight 데이터에서 (link, title)을 추출."""
    result_list: List[Tuple[str, str]] = []
    for m in ITEM_PATTERN.finditer(content):
        title = m.group("title")
        link = url_prefix + m.group("url")
        result_list.append((link, title))
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

    content = IO.read_stdin()
    result_list = parse_feed_list(content)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemNavercast(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 30)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "7"]), 7)

            # --- parse_feed_list ---

            def test_parse_feed_list_basic(self):
                content = r"\"publicId\":\"abc\",\"title\":\"My Title\",\"url\":\"/한국-역사-문화/my-title-abc\""
                self.assertEqual(
                    parse_feed_list(content),
                    [
                        (
                            "https://terms.naver.com/한국-역사-문화/my-title-abc",
                            "My Title",
                        )
                    ],
                )

            def test_parse_feed_list_multiple(self):
                content = (
                    r"\"publicId\":\"abc\",\"title\":\"A\",\"url\":\"/한국-역사-문화/a-abc\"},"
                    r"{\"publicId\":\"def\",\"title\":\"B\",\"url\":\"/한국-역사-문화/b-def\""
                )
                self.assertEqual([t for _, t in parse_feed_list(content)], ["A", "B"])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list(""), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 30), ["l1\tA", "l2\tB"]
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 https://terms.naver.com/한국-역사-문화 를 받아온 실제
            #       flight 데이터 중 레코드 3개(유일한/대조영/윤봉길)만 샘플링.
            # 기대 출력: 동일 입력을 'capture_item_navercast.py -n 5'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_TEXT = '\\"publicId\\":\\"2JzRZNU1IqaElHw5y9V80l\\",\\"gdid\\":\\"00102500_0042981292304965118\\",\\"title\\":\\"유일한\\",\\"titleHtml\\":\\"유일한\\",\\"foreignTitles\\":[{\\"lang\\":\\"ko\\",\\"text\\":\\"柳一韓\\"}],\\"category\\":{\\"id\\":\\"69200b43e430423a274c6b96\\",\\"title\\":\\"한국 역사·문화\\"},\\"summary\\":\\"“우리는 공평한 기회, 합리적인 경제정책, 세계 각국과의 자유로운 교역 등 전체 국민생활의 제한없는 발전을 위해 가장 유망한 여건을 형성시키는 민주주의의 기본원칙에 전적으로 따르고 있다.” «우리는 공평한 기회, 합리적인 경제정책, 세계 각국과의 자유로운 교역 등 전체 국민생활의 제한없는 발전을 위해 가장 유망한 여건을 형성시키는 민주주의의 기본원칙에 전적으로 따르고 있다. -1919년 4월 한인자유대회에서 선생이 작성한 결의문 내용 중에서-» 국권수호를 위해 선생의 부친은 아들을 유학시키기로 결심: 유일한(柳一韓, 1895. 1. 15~19\\",\\"url\\":\\"/한국-역사-문화/유일한-2JzRZNU1IqaElHw5y9V80l\\",\\"likeCount\\":0,\\"source\\":{\\"title\\":\\"독립운동가\\",\\"id\\":\\"038EBomVa9nn7aZ6N1WshG\\"},\\"author\\":\\"$undefined\\",\\"thumb\\":{\\"url\\":\\"https://nterms-phinf.pstatic.net/MjAyNjAzMjlfMTMz/MDAxNzc0NzIxOTQ0NTYx.ulU0CfnJUQn7OkHiKMKY5sieGWHA5x0l0cAbREA7LAYg.U3KhMBFRuo8uSN8lbYnEHOwmQYWlwzt0bcKbpSxGy4Ug.JPEG/20170316145228985_MD5CUVZE4.jpg\\",\\"width\\":240,\\"height\\":240,\\"ratio\\":1,\\"faceCount\\":1,\\"useWatermark\\":false,\\"watermarkKey\\":null},\\"contentType\\":\\"doc\\",\\"subInfoType\\":\\"$undefined\\",\\"vid\\":\\"$undefined\\",\\"shortsUrl\\":\\"$undefined\\",\\"clipId\\":\\"$undefined\\",\\"isNaverTV\\":\\"$undefined\\",\\"videoDuration\\":\\"$undefined\\",\\"isLiked\\":false},{\\"publicId\\":\\"35hMkDZ4iGgAMGf7l5usfw\\",\\"gdid\\":\\"00102500_002131126681\\",\\"title\\":\\"대조영\\",\\"titleHtml\\":\\"대조영\\",\\"foreignTitles\\":[{\\"lang\\":\\"ko\\",\\"text\\":\\"大祚榮\\"}],\\"category\\":{\\"id\\":\\"69200b43e430423a274c6b96\\",\\"title\\":\\"한국 역사·문화\\"},\\"summary\\":\\"대조영과 발해는 오랫동안 우리 역사에서 잊혀 있었다. 고구려의 정통성을 계승하여 15대 230년을 지속해온 발해는 삼국을 통일한 신라와 함께, 우리 역사의 유일한 남북국 시대를 이뤘다. 대조영(大祚榮, ?~719, 재위 698~719)과 발해는 오랫동안 우리 역사에서 잊혀 있었다. 발해가 멸망하고 나서그 유민들은 강제로 이주하였고 수도였던 동경성은 불타버려 발해인들의 역사는 후세에 전해지지 못했다. 그러나 근래의 연구는 만주∙연해주∙북한을 아우르는 대제국을 건설했던 발해, 독립된 연호를 사용하고 황제국을 칭했던 발해가 분명히 고구려인이 세\\",\\"url\\":\\"/한국-역사-문화/대조영-35hMkDZ4iGgAMGf7l5usfw\\",\\"likeCount\\":0,\\"source\\":{\\"title\\":\\"인물한국사\\",\\"id\\":\\"2hVJxmlnoaPU9OHyZ02VK9\\"},\\"author\\":\\"$undefined\\",\\"thumb\\":{\\"url\\":\\"https://nterms-phinf.pstatic.net/MjAyNjAzMjlfMjcg/MDAxNzc0NzIxOTM0NTMz.pqxASx4EAryrjUrrH8WSXUygbz7kK_vTqaoqvqD0Rkgg.iBQJh4IKwOxywsbHTh4oi4I4RYhXxlzeyltlAeX_qV8g.JPEG/20170316144940345_7XE00Z3NU.jpg\\",\\"width\\":240,\\"height\\":240,\\"ratio\\":1,\\"faceCount\\":0,\\"useWatermark\\":false,\\"watermarkKey\\":null},\\"contentType\\":\\"doc\\",\\"subInfoType\\":\\"$undefined\\",\\"vid\\":\\"$undefined\\",\\"shortsUrl\\":\\"$undefined\\",\\"clipId\\":\\"$undefined\\",\\"isNaverTV\\":\\"$undefined\\",\\"videoDuration\\":\\"$undefined\\",\\"isLiked\\":false},{\\"publicId\\":\\"2uI2ysmVNacw2ebFINmRhA\\",\\"gdid\\":\\"08111A81_0052411303696705280\\",\\"title\\":\\"윤봉길\\",\\"titleHtml\\":\\"윤봉길\\",\\"foreignTitles\\":[{\\"lang\\":\\"ko\\",\\"text\\":\\"尹奉吉\\"}],\\"category\\":{\\"id\\":\\"69200b43e430423a274c6b96\\",\\"title\\":\\"한국 역사·문화\\"},\\"summary\\":\\"19세의 나이에 이미 농촌계몽운동에 뛰어든 의사는 계몽운동만으로는 독립을 이룰 수 없다는 한계를 인식하고 중국으로 망명길에 오른다. 그곳에서 백범 김구를 만난 의사는 의열투쟁에 뜻을 모으고 한인애국단에 가입, 홍구공원 거사를 계획한다. 19세의 나이에 이미 농촌계몽운동에 뛰어든 윤봉길 의사는 야학당을 개설하여 한글 교육 등 문맹 퇴치와 민족의식 고취에 심혈을 기울였다. 하지만 계몽운동만으로는 독립을 이룰 수 없다는 한계를 인식하고 중국으로 망명길에 오른다. 그곳에서 백범 김구를 만난 윤 의사는 의열투쟁에 뜻을 모으고 한인애국단에 가입, 김구와 함께 홍구공원 거사를 계획한다. 윤 의사의 의\\",\\"url\\":\\"/한국-역사-문화/윤봉길-2uI2ysmVNacw2ebFINmRhA\\",\\"likeCount\\":0,\\"source\\":{\\"title\\":\\"독립운동가\\",\\"id\\":\\"038EBomVa9nn7aZ6N1WshG\\"},\\"author\\":\\"$undefined\\",\\"thumb\\":{\\"url\\":\\"https://nterms-phinf.pstatic.net/MjAyNjAzMjlfMTI2/MDAxNzc0NzIxOTQ5NDkz.X0AK-d4xuPCUKExCi5cZrupTpYaKd2Ctc2_syiicWTAg.abVLUnVXFwyIhiicboG5yk40ifhggw44zIRlSxfLqXYg.JPEG/20170316145351181_2O8PGSX95.jpg\\",\\"width\\":240,\\"height\\":240,\\"ratio\\":1,\\"faceCount\\":1,\\"useWatermark\\":false,\\"watermarkKey\\":null},\\"contentType\\":\\"doc\\",\\"subInfoType\\":\\"$undefined\\",\\"vid\\":\\"$undefined\\",\\"shortsUrl\\":\\"$undefined\\",\\"clipId\\":\\"$undefined\\",\\"isNaverTV\\":\\"$undefined\\",\\"videoDuration\\":\\"$undefined\\",\\"isLiked\\":false}'

            def test_real_sample_end_to_end(self):
                result = parse_feed_list(self.REAL_SAMPLE_TEXT)
                lines = render_lines(result, 5)
                self.assertEqual(
                    lines,
                    [
                        "https://terms.naver.com/한국-역사-문화/유일한-2JzRZNU1IqaElHw5y9V80l\t유일한",
                        "https://terms.naver.com/한국-역사-문화/대조영-35hMkDZ4iGgAMGf7l5usfw\t대조영",
                        "https://terms.naver.com/한국-역사-문화/윤봉길-2uI2ysmVNacw2ebFINmRhA\t윤봉길",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
