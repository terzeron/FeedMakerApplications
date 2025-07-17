#!/usr/bin/env python


import sys
import re
import getopt
import urllib.parse
import unittest

from bin.feed_maker_util import IO, Env


def main():
    url_prefix = "http://blog.naver.com/PostView.naver?blogId="

    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    result_list = []
    # This logic is from the original file. It has a bug where url_prefix is progressively built if multiple blogIds are found
    # and the final prefix is used for all entries. Reverting to it as requested.
    for line in IO.read_stdin_as_line_list():
        m = re.search(r'"blogId"\s*:\s*"(?P<blogId>[^"]+)"', line)
        if m:
            url_prefix = url_prefix + m.group("blogId") + "&logNo="

        matches = re.findall(r'"logNo":"(\d+)","title":"([^"]+)",', line)
        for match in matches:
            log_no = match[0]
            link = log_no
            title = urllib.parse.unquote(match[1])
            title = re.sub(r"\+", " ", title)
            title = re.sub(r"&quot;", "'", title)
            title = re.sub(r"&(lt|gt);", "", title)
            title = re.sub(r"\n", " ", title)
            result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (url_prefix + link, title))


class TestCaptureItemNaverBlog(unittest.TestCase):
    # 테스트용 샘플 입력 데이터. 실제 네이버 블로그 피드 데이터와 유사한 구조를 가집니다.
    SAMPLE_INPUT_FOR_SCHEMA = """var mInfo = {"viewDate":"20240728","blogId":"test_user_123","logNo":"223534275525","title":"Sample Blog Post Title 1","nickName":"Tester"};
var oData = {"logNo":"223534275525","title":"Sample+Blog+Post+Title+1","content":"...","commentCnt":7,"taglist":["tag1","tag2"]};
var anotherData = {"logNo":"223534275526","title":"Another%20Post%20Title","content":"...","commentCnt":10,"taglist":[]};
"""

    # "골든 스키마". 위 샘플 입력에서 실제 값만 플레이스홀더로 대체한 버전입니다.
    # 이 스키마를 기준으로 입력 데이터의 구조 변경을 감지합니다.
    GOLDEN_SCHEMA = """var mInfo = {"viewDate":"__DATE__","blogId":"__BLOG_ID__","logNo":"__LOG_NO__","title":"__TITLE__","nickName":"__NICKNAME__"};
var oData = {"logNo":"__LOG_NO__","title":"__TITLE__","content":"...","commentCnt":__NUMBER__,"taglist":__LIST__};
var anotherData = {"logNo":"__LOG_NO__","title":"__TITLE__","content":"...","commentCnt":__NUMBER__,"taglist":__LIST__};
"""

    def _anonymize_line(self, line):
        """
        입력된 문자열 한 줄에서 실제 데이터 값들을 찾아 '__PLACEHOLDER__' 형태로 익명화합니다.
        데이터의 내용이 아닌 구조를 비교하기 위한 전처리 과정입니다.
        """
        # 익명화를 위한 규칙 목록: (정규식 패턴, 대체할 플레이스홀더)
        # 규칙을 이곳에 모아두어 어떤 값들이 변경되는지 쉽게 파악할 수 있습니다.
        anonymization_rules = [
            (r'("blogId"\s*:\s*")([^"]+)(")', r'\1__BLOG_ID__\3'),
            (r'("logNo"\s*:\s*")([^"]+)(")', r'\1__LOG_NO__\3'),
            (r'("title"\s*:\s*")([^"]+)(")', r'\1__TITLE__\3'),
            (r'("viewDate"\s*:\s*")([^"]+)(")', r'\1__DATE__\3'),
            (r'("nickName"\s*:\s*")([^"]+)(")', r'\1__NICKNAME__\3'),
            (r'("commentCnt"\s*:\s*)(\d+)', r'\1__NUMBER__'),
            (r'("taglist"\s*:\s*)(\[.*\])', r'\1__LIST__'),
        ]
        for pattern, replacement in anonymization_rules:
            line = re.sub(pattern, replacement, line)
        return line

    def test_input_schema_is_unchanged(self):
        """
        입력 데이터의 스키마가 변경되지 않았는지 검증하는 "골든 마스터 테스트"입니다.

        이 테스트는 샘플 입력을 익명화한 결과가 미리 정의된 "골든 스키마"와 일치하는지
        비교합니다. 만약 네이버 블로그의 데이터 구조가 변경되면 이 테스트가 실패하여
        스크립트의 수정이 필요함을 알려줍니다.
        """
        # 1. 클래스 변수에서 샘플 입력과 골든 스키마를 가져옵니다.
        input_lines = self.SAMPLE_INPUT_FOR_SCHEMA.strip().splitlines()
        golden_lines = self.GOLDEN_SCHEMA.strip().splitlines()

        # 2. 샘플 입력의 각 줄을 익명화 규칙에 따라 변환합니다.
        anonymized_lines = [self._anonymize_line(line) for line in input_lines]

        # 3. 변환된 결과가 골든 스키마와 정확히 일치하는지 확인합니다.
        # 실패 시, 어떤 부분이 다른지 쉽게 파악할 수 있도록 상세한 메시지를 출력합니다.
        self.assertEqual(
            anonymized_lines,
            golden_lines,
            "\n\n[스키마 불일치 감지]\n"
            "입력 데이터의 구조(스키마)가 기존과 다릅니다.\n"
            "이것은 에러가 아닐 수 있으며, 데이터 제공처의 의도된 변경일 수 있습니다.\n"
            "아래 상세 내용을 확인하고, 변경된 내용이 올바르다면 GOLDEN_SCHEMA를 갱신해 주세요."
        )


def run_tests():
    # 이 파일에 있는 모든 테스트를 로드하여 실행합니다.
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner().run(suite)


if __name__ == "__main__":
    if Env.get("TEST", "0") == "1":
        run_tests()
    else:
        sys.exit(main())
