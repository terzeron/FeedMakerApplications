#!/usr/bin/env python


import os
import math
import sys
import re
import getopt
import json
from typing import List, NamedTuple

from bin.feed_maker_util import IO


URL_PREFIX_TEMPLATE = "https://m.cafe.naver.com/ca-fe/web/cafes/%d/articles/%d"


class Options(NamedTuple):
    num_of_recent_feeds: int
    threshold: float
    average: float
    stdev: float
    top_ratio: float
    include_private: bool


def parse_args(argv: List[str]) -> Options:
    """명령행 인자를 파싱해 Options로 반환."""
    num_of_recent_feeds = 30
    threshold = 0.0
    average = 0.0
    stdev = 1.0
    top_ratio = 0.0
    include_private = False
    optlist, _ = getopt.getopt(argv, "n:f:t:a:s:r:p")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-t":
            threshold = float(a)
        elif o == "-a":
            average = float(a)
        elif o == "-s":
            stdev = float(a)
        elif o == "-r":
            top_ratio = float(a)
        elif o == "-p":
            include_private = True
    return Options(
        num_of_recent_feeds, threshold, average, stdev, top_ratio, include_private
    )


def build_candidates(
    data: dict, url_prefix_template: str = URL_PREFIX_TEMPLATE
) -> list:
    """articleList에서 후보 튜플(link, title, blind, open, restrict, read, like, comment, score)을 만든다."""
    candidates: list = []
    if "result" in data and "articleList" in data["result"]:
        for article in data["result"]["articleList"]:
            if "item" in article:
                item = article["item"]
                article_id = item["articleId"]
                cafe_id = item["cafeId"]
                link = url_prefix_template % (cafe_id, article_id)
                nickname = re.sub(r"\n", "", item["writerInfo"]["nickName"].strip())
                subject = re.sub(r"\n", "", item["subject"].strip())
                title = f"{nickname}: {subject}"
                read_count = int(item["readCount"])
                like_count = int(item["likeCount"])
                comment_count = int(item["commentCount"])
                score = read_count + 5 * like_count + 50 * comment_count
                candidates.append(
                    (
                        link,
                        title,
                        item["blindArticle"],
                        item["openArticle"],
                        item["restrictMenu"],
                        item["readCount"],
                        item["likeCount"],
                        item["commentCount"],
                        score,
                    )
                )
    return candidates


def select_candidates(
    candidates: list, top_ratio: float, threshold: float, average: float, stdev: float
) -> list:
    """top_ratio 또는 z-score threshold로 후보를 거른 뒤 score 항목을 제외한 튜플 목록을 반환."""
    result_list: list = []
    if 0.0 < top_ratio <= 100.0 and candidates:
        scores = sorted([c[-1] for c in candidates], reverse=True)
        cutoff_idx = max(1, int(math.ceil(len(scores) * top_ratio / 100.0))) - 1
        score_cutoff = scores[cutoff_idx]
        for c in candidates:
            if c[-1] >= score_cutoff:
                result_list.append(c[:-1])
    elif threshold > 0.0 and candidates:
        for c in candidates:
            z = (c[-1] - average) / stdev
            if z >= threshold:
                result_list.append(c[:-1])
    else:
        result_list = [c[:-1] for c in candidates]
    return result_list


def render_lines(
    result_list: list, num_of_recent_feeds: int, include_private: bool
) -> List[str]:
    """blind/restrict/open 조건을 적용해 'link\\ttitle\\tread\\tlike\\tcomment' 라인 목록을 만든다."""
    lines: List[str] = []
    for (
        link,
        title,
        blind,
        open_,
        restrict,
        read_count,
        like_count,
        comment_count,
    ) in result_list[:num_of_recent_feeds]:
        if not blind and not restrict and (open_ or include_private):
            lines.append(
                f"{link}\t{title}\t{read_count}\t{like_count}\t{comment_count}"
            )
    return lines


def main():
    opts = parse_args(sys.argv[1:])

    content = IO.read_stdin()
    result_list: list = []
    try:
        data = json.loads(content)
        candidates = build_candidates(data)
        result_list = select_candidates(
            candidates, opts.top_ratio, opts.threshold, opts.average, opts.stdev
        )
    except json.JSONDecodeError:
        pass  # Ignore invalid JSON

    for line in render_lines(
        result_list, opts.num_of_recent_feeds, opts.include_private
    ):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        def _item(
            article_id=1,
            cafe_id=10,
            nick="N",
            subject="S",
            read=100,
            like=5,
            comment=2,
            blind=False,
            open_=True,
            restrict=False,
        ):
            return {
                "item": {
                    "articleId": article_id,
                    "cafeId": cafe_id,
                    "writerInfo": {"nickName": nick},
                    "subject": subject,
                    "readCount": read,
                    "likeCount": like,
                    "commentCount": comment,
                    "blindArticle": blind,
                    "openArticle": open_,
                    "restrictMenu": restrict,
                }
            }

        class TestCaptureItemNaverCafe(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_defaults(self):
                opts = parse_args([])
                self.assertEqual(opts, Options(30, 0.0, 0.0, 1.0, 0.0, False))

            def test_parse_args_all(self):
                opts = parse_args(
                    ["-n", "5", "-t", "1.5", "-a", "10", "-s", "2", "-r", "20", "-p"]
                )
                self.assertEqual(opts, Options(5, 1.5, 10.0, 2.0, 20.0, True))

            # --- build_candidates ---

            def test_build_candidates_basic(self):
                data = {
                    "result": {
                        "articleList": [
                            _item(article_id=1, cafe_id=10, nick="bob", subject="hi")
                        ]
                    }
                }
                c = build_candidates(data)
                self.assertEqual(len(c), 1)
                self.assertEqual(
                    c[0][0], "https://m.cafe.naver.com/ca-fe/web/cafes/10/articles/1"
                )
                self.assertEqual(c[0][1], "bob: hi")

            def test_build_candidates_score(self):
                data = {"result": {"articleList": [_item(read=100, like=5, comment=2)]}}
                # score = 100 + 5*5 + 50*2 = 225
                self.assertEqual(build_candidates(data)[0][-1], 225)

            def test_build_candidates_strips_newlines(self):
                data = {"result": {"articleList": [_item(nick="a\nb", subject="\nc ")]}}
                self.assertEqual(build_candidates(data)[0][1], "ab: c")

            def test_build_candidates_no_articles(self):
                self.assertEqual(build_candidates({}), [])

            # --- select_candidates ---

            def _cands(self):
                # (..., score) 형태의 최소 후보들
                return [
                    ("l1", "t1", False, True, False, 0, 0, 0, 300),
                    ("l2", "t2", False, True, False, 0, 0, 0, 200),
                    ("l3", "t3", False, True, False, 0, 0, 0, 100),
                ]

            def test_select_candidates_default_returns_all(self):
                result = select_candidates(self._cands(), 0.0, 0.0, 0.0, 1.0)
                self.assertEqual(len(result), 3)
                self.assertEqual(len(result[0]), 8)  # score 제거됨

            def test_select_candidates_top_ratio(self):
                # 상위 34% → ceil(3*0.34)=2 → 상위 2개(>=200)
                result = select_candidates(self._cands(), 34.0, 0.0, 0.0, 1.0)
                self.assertEqual([r[0] for r in result], ["l1", "l2"])

            def test_select_candidates_threshold(self):
                # avg=100, sd=100 → z = (score-100)/100; threshold=1 → score>=200
                result = select_candidates(self._cands(), 0.0, 1.0, 100.0, 100.0)
                self.assertEqual([r[0] for r in result], ["l1", "l2"])

            # --- render_lines ---

            def test_render_lines_basic(self):
                result_list = [("l1", "t1", False, True, False, 100, 5, 2)]
                self.assertEqual(
                    render_lines(result_list, 30, False), ["l1\tt1\t100\t5\t2"]
                )

            def test_render_lines_skips_blind(self):
                result_list = [("l1", "t1", True, True, False, 1, 1, 1)]
                self.assertEqual(render_lines(result_list, 30, False), [])

            def test_render_lines_skips_restricted(self):
                result_list = [("l1", "t1", False, True, True, 1, 1, 1)]
                self.assertEqual(render_lines(result_list, 30, False), [])

            def test_render_lines_private_requires_flag(self):
                result_list = [("l1", "t1", False, False, False, 1, 1, 1)]
                self.assertEqual(render_lines(result_list, 30, False), [])
                self.assertEqual(len(render_lines(result_list, 30, True)), 1)

        class TestNaverCafeSchema(unittest.TestCase):
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
      }
    ]
  }
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
                sample_data = json.loads(self.SAMPLE_INPUT_FOR_SCHEMA)
                golden_schema = self._anonymize_recursive(sample_data)
                self.assertEqual(self._anonymize_recursive(sample_data), golden_schema)

            # --- end-to-end with real sampled crawl data ---
            # 입력: crawler.py로 apis.naver.com cafe-boardlist-api(cafeId=10503958) 응답에서
            #       파서가 읽는 result.articleList[].item 필드만 3개로 샘플링.
            # 기대 출력: threshold/top_ratio 없이(=전부 통과) build_candidates→select_candidates→
            #          render_lines로 만든 'link\ttitle\tread\tlike\tcomment' 라인.
            REAL_SAMPLE_DATA = {
                "result": {
                    "articleList": [
                        {
                            "item": {
                                "articleId": 406400,
                                "cafeId": 10503958,
                                "writerInfo": {"nickName": "하비팤"},
                                "subject": "M1068A3 제작기(3)",
                                "readCount": 0,
                                "likeCount": 0,
                                "commentCount": 0,
                                "blindArticle": False,
                                "openArticle": True,
                                "restrictMenu": False,
                            }
                        },
                        {
                            "item": {
                                "articleId": 406391,
                                "cafeId": 10503958,
                                "writerInfo": {"nickName": "제프티"},
                                "subject": "K21 보병전투차 #9 - 깨작 깨작",
                                "readCount": 70,
                                "likeCount": 4,
                                "commentCount": 0,
                                "blindArticle": False,
                                "openArticle": True,
                                "restrictMenu": False,
                            }
                        },
                        {
                            "item": {
                                "articleId": 406388,
                                "cafeId": 10503958,
                                "writerInfo": {"nickName": "jump7221"},
                                "subject": "트럼페터 포르쉐 킹타이거에서 가지고온~~~",
                                "readCount": 82,
                                "likeCount": 3,
                                "commentCount": 0,
                                "blindArticle": False,
                                "openArticle": True,
                                "restrictMenu": False,
                            }
                        },
                    ]
                }
            }

            def test_real_sample_end_to_end(self):
                candidates = build_candidates(self.REAL_SAMPLE_DATA)
                result_list = select_candidates(candidates, 0.0, 0.0, 0.0, 1.0)
                lines = render_lines(result_list, 30, False)
                self.assertEqual(
                    lines,
                    [
                        "https://m.cafe.naver.com/ca-fe/web/cafes/10503958/articles/406400\t하비팤: M1068A3 제작기(3)\t0\t0\t0",
                        "https://m.cafe.naver.com/ca-fe/web/cafes/10503958/articles/406391\t제프티: K21 보병전투차 #9 - 깨작 깨작\t70\t4\t0",
                        "https://m.cafe.naver.com/ca-fe/web/cafes/10503958/articles/406388\tjump7221: 트럼페터 포르쉐 킹타이거에서 가지고온~~~\t82\t3\t0",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
