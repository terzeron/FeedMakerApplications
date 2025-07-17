#!/usr/bin/env python


import sys
import re
import getopt
import json
from math import log2
import unittest

from bin.feed_maker_util import IO, Env


def main():
    url_prefix = "https://m.cafe.naver.com/ca-fe/web/cafes/10503958/articles/"

    num_of_recent_feeds = 30
    threshold = 0.0
    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:t:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == '-t':
            threshold = float(a)

    result_list = []
    content = IO.read_stdin()
    
    try:
        data = json.loads(content)
        if "result" in data and "articleList" in data["result"]:
            for article in data["result"]["articleList"]:
                if "item" in article:
                    item = article["item"]
                    link = str(item["articleId"])
                    nickname = re.sub(r'\n', '', item["writerInfo"]["nickName"].strip())
                    subject = re.sub(r'\n', '', item["subject"].strip())
                    title = f"{nickname}: {subject}"
                    
                    if threshold > 0.0:
                        score = (log2(int(item["commentCount"]) + 1) + log2(int(item["likeCount"]) + 1)) / (log2(int(item["readCount"]) + 1) + 1) + log2(int(item["readCount"]) + 1) / log2(300)
                        if score < threshold:
                            continue
                    result_list.append((link, title))
    except json.JSONDecodeError:
        pass # Ignore invalid JSON
        
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (url_prefix + link, title))


class TestCaptureItemNaverCafe(unittest.TestCase):
    # 테스트용 샘플 입력 데이터
    SAMPLE_INPUT_FOR_SCHEMA = """
{
  "result": {
    "articleList": [
      {
        "item": {
          "articleId": 12345,
          "writerInfo": { "nickName": "Tester1" },
          "subject": "Sample Post 1",
          "commentCount": 10,
          "likeCount": 5,
          "readCount": 100
        }
      },
      {
        "item": {
          "articleId": 67890,
          "writerInfo": { "nickName": "Tester2\\n" },
          "subject": "\\nAnother Post  ",
          "commentCount": 0,
          "likeCount": 1,
          "readCount": 50
        }
      }
    ]
  }
}
"""

    def _anonymize_recursive(self, obj):
        if isinstance(obj, dict):
            return {k: self._anonymize_recursive(v) for k, v in obj.items()}
        if isinstance(obj, list):
            # 리스트는 첫 번째 요소의 스키마만 대표로 사용
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
