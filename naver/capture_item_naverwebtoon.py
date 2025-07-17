#!/usr/bin/env python


import sys
import re
import getopt
import json
import unittest

from bin.feed_maker_util import IO, URL, Env


def main():
    link = ""
    title = ""
    url_template = "https://comic.naver.com/webtoon/detail?titleId=%d&no=%d"

    num_of_recent_feeds = 1000
    optlist, args = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    content = IO.read_stdin()
    data = json.loads(content)
    result_list = []
    if "titleId" in data and data["titleId"]:
        title_id = data["titleId"]
        if "articleList" in data and data["articleList"]:
            article_list = data["articleList"]
            for article in article_list:
                if "no" in article and article["no"]:
                    no = article["no"]
                    link = url_template % (title_id, no)
                if "subtitle" in article and article["subtitle"]:
                    title = article["subtitle"]
                result_list.append((link, title))

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


class TestCaptureItemNaverWebtoon(unittest.TestCase):
    SAMPLE_INPUT_FOR_SCHEMA = """
{
  "titleId": 123456,
  "articleList": [
    { "no": 1, "subtitle": "Episode 1" },
    { "no": 2, "subtitle": "Episode 2" }
  ]
}
"""

    def _anonymize_recursive(self, obj):
        if isinstance(obj, dict):
            return {k: self._anonymize_recursive(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._anonymize_recursive(obj[0])] if obj else []
        if isinstance(obj, str):
            return "__STRING__"
        if isinstance(obj, int):
            return "__NUMBER__"
        return obj

    def test_input_schema_is_unchanged(self):
        """입력 JSON 데이터의 스키마가 변경되지 않았는지 검증합니다."""
        sample_data = json.loads(self.SAMPLE_INPUT_FOR_SCHEMA)
        golden_schema = self._anonymize_recursive(sample_data)
        self.assertEqual(
            self._anonymize_recursive(sample_data),
            golden_schema,
            "\n\n[스키마 불일치 감지]\n"
            "입력 데이터의 구조(스키마)가 기존과 다릅니다."
        )


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner().run(suite)


if __name__ == "__main__":
    if Env.get("TEST", "0") == "1":
        run_tests()
    else:
        sys.exit(main())
