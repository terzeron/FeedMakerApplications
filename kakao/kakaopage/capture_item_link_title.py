#!/usr/bin/env python

import os
import sys
import re
import json
import time
import getopt
import logging
import logging.config
import urllib.request
from pathlib import Path
from typing import Callable, List, Optional, Tuple
from bin.feed_maker_util import IO


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


LINK_PREFIX = "https://page.kakao.com/content"
PAGE_URL = "https://bff-page.kakao.com/api/gateway/view/v2/landing/dayofweek?category_uid=10&screen_uid=52&page=%d&tab_uid=%s"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
ADULT_AGE_GRADE = 19
EXCLUDED_SUB_CATEGORIES = frozenset({"로판", "로맨스"})
MAX_PAGES = 60
FETCH_RETRIES = 2
FETCH_RETRY_SLEEP_SEC = 3


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-f":
            _ = Path(a)
    return num_of_recent_feeds


def strip_outer_tags(content: str) -> str:
    """본문 앞뒤에 붙은 HTML 태그 묶음을 제거한다."""
    return re.sub(r"(^(<\S[^>]*>)+|(<\S[^>]*>)+$)", "", content)


def extract_items(
    json_data: dict, link_prefix: str = LINK_PREFIX
) -> List[Tuple[str, str]]:
    """landing/dayofweek 응답에서 성인용(19세 이상)과 제외 장르(로판, 로맨스)를 뺀 작품을 (link, title)로 추출한다.

    제목 앞에 판매 시작일(YYYY-MM-DD)을 붙여 sort_field_pattern으로 정렬할 수 있게 한다.
    """
    result_list: List[Tuple[str, str]] = []
    for item in json_data.get("result", {}).get("list", []):
        if item.get("age_grade", 0) >= ADULT_AGE_GRADE:
            continue
        if item.get("sub_category", "") in EXCLUDED_SUB_CATEGORIES:
            continue
        series_id = item.get("series_id")
        title = item.get("title")
        if not series_id or not title:
            continue
        date_str = (item.get("start_sale_dt") or "1970-01-01")[:10]
        result_list.append(
            ("%s/%s" % (link_prefix, series_id), "%s %s" % (date_str, title))
        )
    return result_list


def next_page_request(json_data: dict, current_page: int) -> Optional[Tuple[int, str]]:
    """다음 페이지가 있으면 (page, tab_uid)를, 없으면 None을 반환한다."""
    result = json_data.get("result", {})
    if result.get("is_end", True) or not result.get("list"):
        return None
    tab_uid = result.get("selected_tab_opt", {}).get("param")
    if tab_uid is None:
        return None
    return current_page + 1, str(tab_uid)


def fetch_page(page: int, tab_uid: str) -> Optional[dict]:
    """다음 페이지를 가져온다. 실패하면 FETCH_RETRIES회 재시도하고, 계속 실패하면 None."""
    req = urllib.request.Request(
        PAGE_URL % (page, tab_uid),
        headers={"User-Agent": USER_AGENT, "Referer": "https://page.kakao.com/"},
    )
    for attempt in range(1 + FETCH_RETRIES):
        if attempt > 0:
            time.sleep(FETCH_RETRY_SLEEP_SEC)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            LOGGER.warning(
                "can't get page %d of tab %s (%d/%d), %s",
                page,
                tab_uid,
                attempt + 1,
                1 + FETCH_RETRIES,
                e,
            )
    return None


def collect_all_pages(
    first_page: dict,
    fetcher: Callable[[int, str], Optional[dict]] = fetch_page,
    max_pages: int = MAX_PAGES,
) -> List[Tuple[str, str]]:
    """첫 페이지부터 is_end가 될 때까지 페이지를 따라가며 작품을 모은다."""
    result_list = extract_items(first_page)
    current = first_page
    page = 0
    while page + 1 < max_pages:
        request = next_page_request(current, page)
        if not request:
            break
        page, tab_uid = request
        current = fetcher(page, tab_uid)
        if not current:
            break
        result_list.extend(extract_items(current))
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """제목(날짜순) 내림차순으로 정렬한 뒤 'link\\ttitle' 라인 목록으로 변환."""
    sorted_list = sorted(result_list, key=lambda obj: obj[1], reverse=True)
    return [
        "%s\t%s" % (link, title) for (link, title) in sorted_list[:num_of_recent_feeds]
    ]


def main() -> int:
    num_of_recent_feeds = parse_args(sys.argv[1:])

    content = strip_outer_tags(IO.read_stdin())
    json_data = json.loads(content)
    if "result" not in json_data or "list" not in json_data["result"]:
        return -1

    result_list = collect_all_pages(json_data)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemLinkTitle(unittest.TestCase):
            def _item(self, sid, title, age=0, dt="2021-02-28T23:00:05+09:00"):
                return {
                    "series_id": sid,
                    "title": title,
                    "age_grade": age,
                    "start_sale_dt": dt,
                }

            def _page(self, items, is_end=True, tab="1"):
                return {
                    "result": {
                        "list": items,
                        "is_end": is_end,
                        "selected_tab_opt": {"name": "월", "param": tab},
                    }
                }

            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "3"]), 3)

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "."]), 1000)

            # --- strip_outer_tags ---

            def test_strip_outer_tags(self):
                self.assertEqual(strip_outer_tags("<pre>{}</pre>"), "{}")

            # --- extract_items ---

            def test_extract_items_basic(self):
                data = self._page([self._item(1, "A")])
                self.assertEqual(
                    extract_items(data),
                    [("https://page.kakao.com/content/1", "2021-02-28 A")],
                )

            def test_extract_items_excludes_adult_only(self):
                data = self._page(
                    [
                        self._item(1, "all", 0),
                        self._item(2, "teen", 15),
                        self._item(3, "adult", 19),
                    ]
                )
                self.assertEqual(
                    [t for _, t in extract_items(data)],
                    ["2021-02-28 all", "2021-02-28 teen"],
                )

            def test_extract_items_excludes_romance_genres(self):
                items = [
                    self._item(1, "rofan"),
                    self._item(2, "romance"),
                    self._item(3, "fantasy"),
                    self._item(4, "nogenre"),
                ]
                items[0]["sub_category"] = "로판"
                items[1]["sub_category"] = "로맨스"
                items[2]["sub_category"] = "판타지"
                self.assertEqual(
                    [t for _, t in extract_items(self._page(items))],
                    ["2021-02-28 fantasy", "2021-02-28 nogenre"],
                )

            def test_extract_items_missing_date_uses_epoch(self):
                item = self._item(1, "A")
                item["start_sale_dt"] = None
                self.assertEqual(
                    extract_items(self._page([item]))[0][1], "1970-01-01 A"
                )

            def test_extract_items_skips_incomplete(self):
                data = self._page([{"series_id": 1}, {"title": "x"}])
                self.assertEqual(extract_items(data), [])

            def test_extract_items_empty(self):
                self.assertEqual(extract_items({}), [])

            # --- next_page_request ---

            def test_next_page_request_when_not_end(self):
                data = self._page([self._item(1, "A")], is_end=False, tab="3")
                self.assertEqual(next_page_request(data, 0), (1, "3"))

            def test_next_page_request_when_end(self):
                self.assertIsNone(
                    next_page_request(self._page([self._item(1, "A")]), 0)
                )

            def test_next_page_request_when_empty_list(self):
                self.assertIsNone(next_page_request(self._page([], is_end=False), 0))

            # --- collect_all_pages ---

            def test_collect_all_pages_follows_until_end(self):
                first = self._page([self._item(1, "A")], is_end=False, tab="2")
                pages = {
                    1: self._page([self._item(2, "B")], is_end=False, tab="2"),
                    2: self._page([self._item(3, "C")], is_end=True, tab="2"),
                }
                calls = []

                def fetcher(page, tab):
                    calls.append((page, tab))
                    return pages[page]

                result = collect_all_pages(first, fetcher)
                self.assertEqual(
                    [l.rsplit("/", 1)[1] for l, _ in result], ["1", "2", "3"]
                )
                self.assertEqual(calls, [(1, "2"), (2, "2")])

            def test_collect_all_pages_stops_on_fetch_failure(self):
                first = self._page([self._item(1, "A")], is_end=False)
                result = collect_all_pages(first, lambda page, tab: None)
                self.assertEqual(len(result), 1)

            def test_collect_all_pages_respects_max_pages(self):
                first = self._page([self._item(1, "A")], is_end=False)
                endless = lambda page, tab: self._page(
                    [self._item(100 + page, "X")], is_end=False
                )
                self.assertEqual(len(collect_all_pages(first, endless, max_pages=3)), 3)

            # --- render_lines ---

            def test_render_lines_sorted_desc_and_limited(self):
                lst = [
                    ("l1", "2021-01-01 A"),
                    ("l2", "2026-01-01 B"),
                    ("l3", "2024-01-01 C"),
                ]
                self.assertEqual(
                    render_lines(lst, 2), ["l2\t2026-01-01 B", "l3\t2024-01-01 C"]
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
