#!/usr/bin/env python

import sys
import os
import re
import json
import time
import getopt
import logging
import logging.config
import urllib.request
from pathlib import Path
from typing import List, Optional
from bin.feed_maker_util import IO, URL, header_str, Env
from bin.feed_maker import FeedMaker
from bin.crawler import Crawler


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()

PRODUCT_LIST_URL = "https://bff-page.kakao.com/api/gateway/api/v2/content/product/list?series_id=%s&cursor_index=0&cursor_direction=NEXT&window_size=%d&sort_type=desc"
COVER_URL_PREFIX = "https://dn-img-page.kakao.com/download/resource?kid="
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
RECENT_EPISODE_COUNT = 30
MAX_RETRIES = 2
RETRY_SLEEP_SEC = 5
LOGIN_NOT_REQUIRED = "비로그인 열람 가능"
LOGIN_REQUIRED = "로그인 열람 필수"
EXCLUDED_SUB_CATEGORIES = frozenset({"로판", "로맨스"})


def is_excluded_series(series: dict) -> bool:
    """제외 장르(로판, 로맨스)에 속한 작품이면 True."""
    return series.get("sub_category", "") in EXCLUDED_SUB_CATEGORIES


def parse_series_id(url: str) -> Optional[str]:
    """작품 URL(https://page.kakao.com/content/<id>)에서 series_id를 뽑는다."""
    m = re.search(r"/content/(\d+)", url)
    return m.group(1) if m else None


def classify_login_requirement(episodes: List[dict]) -> str:
    """유료 회차보다 최신인 무료 회차가 있으면 비로그인 열람 가능, 없으면 로그인 열람 필수.

    앞쪽 몇 회만 무료이고 이후는 모두 로그인 창이 뜨는 작품(예: 템빨)은 무료 회차가
    가장 오래된 쪽에만 있으므로 로그인 필수가 된다. 앞쪽 무료 회차 수는 작품마다 달라
    고정값 대신 회차 번호(order_value)의 선후 관계로 판단한다.
    회차 정보가 없으면 판단하지 않고 빈 문자열을 반환한다.
    """
    if not episodes:
        return ""
    non_free_nos = [e.get("order_value", 0) for e in episodes if not e.get("is_free")]
    if not non_free_nos:
        return LOGIN_NOT_REQUIRED
    oldest_non_free_no = min(non_free_nos)
    if any(
        e.get("is_free") and e.get("order_value", 0) > oldest_non_free_no
        for e in episodes
    ):
        return LOGIN_NOT_REQUIRED
    return LOGIN_REQUIRED


def extract_episodes(json_data: dict) -> List[dict]:
    """product/list 응답에서 회차 정보 목록을 뽑는다."""
    return [
        x["item"]
        for x in json_data.get("result", {}).get("list", [])
        if isinstance(x, dict) and "item" in x
    ]


def fetch_product_list(series_id: str) -> Optional[dict]:
    """작품 정보와 최신 회차를 한 번에 가져온다. 실패하면 MAX_RETRIES회 재시도하고, 계속 실패하면 None."""
    req = urllib.request.Request(
        PRODUCT_LIST_URL % (series_id, RECENT_EPISODE_COUNT),
        headers={"User-Agent": USER_AGENT, "Referer": "https://page.kakao.com/"},
    )
    for attempt in range(1 + MAX_RETRIES):
        if attempt > 0:
            time.sleep(RETRY_SLEEP_SEC)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if data.get("result", {}).get("series_item"):
                return data
            LOGGER.warning("no series_item for series '%s'", series_id)
        except Exception as e:
            LOGGER.warning(
                "can't get product list of series '%s' (%d/%d), %s",
                series_id,
                attempt + 1,
                1 + MAX_RETRIES,
                e,
            )
    return None


def compose_description(
    series: dict, link: str, login_status: str = "", cover_url: str = ""
) -> str:
    description = "<div>\n"
    description += "    <div>%s</div>\n" % series["title"]
    if login_status:
        description += "    <div>%s</div>\n" % login_status
    description += "    <div>%s</div>\n" % series.get("sub_category", "")
    description += "    <div>%s</div>\n" % series.get("authors", "")
    description += "    <div>%s</div>\n" % series.get("description", "")[:200]
    description += "    <div><a href='%s'>%s</a></div>\n" % (link, link)
    if cover_url:
        description += "    <div><img src='%s'></div>\n" % cover_url
    description += "</div>\n"
    return description


def download_with_retry(crawler: Crawler, url: str, file_path: Path) -> bool:
    """표지 이미지를 내려받고, 실패하면 5초 간격으로 최대 2회 재시도한다(총 3회 시도)."""
    error = None
    for attempt in range(1 + MAX_RETRIES):
        if attempt > 0:
            time.sleep(RETRY_SLEEP_SEC)
        result, error, _ = crawler.run(url, download_file=file_path)
        if result and not error:
            return True
        if attempt < MAX_RETRIES:
            LOGGER.warning(
                "failed to download cover image '%s' (%s), retrying (%d/%d)...",
                url,
                error,
                attempt + 1,
                MAX_RETRIES,
            )
    LOGGER.warning("can't download cover image '%s' to '%s', %s", url, file_path, error)
    return False


def download_cover(crawler: Crawler, thumbnail: str, item_id: str) -> str:
    """표지를 내려받아 서비스 URL을 반환한다. 실패하면 빈 문자열."""
    download_dir_path = Path(Env.get("WEB_SERVICE_IMAGE_DIR_PREFIX")) / "kakaopage"
    download_dir_path.mkdir(parents=True, exist_ok=True)
    cover_path = download_dir_path / (item_id + ".jpg")
    if not cover_path.is_file() or cover_path.stat().st_size == 0:
        if not download_with_retry(crawler, COVER_URL_PREFIX + thumbnail, cover_path):
            return ""
    return Env.get("WEB_SERVICE_IMAGE_URL_PREFIX") + "/kakaopage/" + cover_path.name


def main() -> int:
    item_url = ""

    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    for o, a in optlist:
        if o == "-f":
            _ = Path(a)
    if args:
        item_url = args[0]

    IO.read_stdin()  # 작품 페이지 HTML은 쓰지 않고 API 결과만 쓴다.

    series_id = parse_series_id(item_url)
    if not series_id:
        LOGGER.error("can't find series id in url '%s'", item_url)
        return -1

    data = fetch_product_list(series_id)
    if not data:
        LOGGER.error("can't get series info of '%s'", series_id)
        return -1
    series = data["result"]["series_item"]
    if "title" not in series:
        LOGGER.error("can't find title of series '%s'", series_id)
        return -1
    if is_excluded_series(series):
        LOGGER.info(
            "skipping excluded sub_category '%s' of series '%s'",
            series["sub_category"],
            series_id,
        )
        return -1

    link = "https://page.kakao.com/content/%s" % series_id
    item_id = URL.get_short_md5_name(URL.get_url_path(link))

    crawler = Crawler()
    cover_url = ""
    if series.get("thumbnail"):
        cover_url = download_cover(crawler, series["thumbnail"], item_id)
    del crawler
    if not cover_url:
        LOGGER.warning("can't download cover image, skipping this feed item")
        return -1

    login_status = classify_login_requirement(extract_episodes(data))
    description = compose_description(series, link, login_status, cover_url)

    print(header_str, end="")
    print(description, end="")
    print(
        FeedMaker.get_image_tag_str("https://terzeron.com", "kakaopage.xml", link),
        end="",
    )

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest
        from unittest import mock

        class TestPostProcessKakaopage(unittest.TestCase):
            def _ep(self, no, free):
                return {"order_value": no, "is_free": free}

            # --- parse_series_id ---

            def test_parse_series_id(self):
                self.assertEqual(
                    parse_series_id("https://page.kakao.com/content/54727849"),
                    "54727849",
                )
                self.assertEqual(
                    parse_series_id("https://page.kakao.com/content/54727849/"),
                    "54727849",
                )
                self.assertIsNone(parse_series_id("https://example.com/x"))

            # --- classify_login_requirement ---

            def test_classify_free_newer_than_paid(self):
                # 레드스톰형: 최신 유료 회차 뒤에 무료 회차가 있고, 더 오래된 유료 회차가 있다.
                eps = [
                    self._ep(487, False),
                    self._ep(482, True),
                    self._ep(470, False),
                ]
                self.assertEqual(classify_login_requirement(eps), LOGIN_NOT_REQUIRED)

            def test_classify_no_free_episode(self):
                eps = [self._ep(348, False), self._ep(330, False)]
                self.assertEqual(classify_login_requirement(eps), LOGIN_REQUIRED)

            def test_classify_only_opening_episodes_free(self):
                # 템빨형: 짧은 작품이라 창에 앞쪽 무료 회차가 들어와도 로그인 필수다.
                eps = [
                    self._ep(8, False),
                    self._ep(6, False),
                    self._ep(5, True),
                    self._ep(2, True),
                ]
                self.assertEqual(classify_login_requirement(eps), LOGIN_REQUIRED)

            def test_classify_all_free(self):
                eps = [self._ep(2, True), self._ep(1, True)]
                self.assertEqual(classify_login_requirement(eps), LOGIN_NOT_REQUIRED)

            def test_classify_unknown_when_no_episodes(self):
                self.assertEqual(classify_login_requirement([]), "")

            # --- is_excluded_series ---

            def test_is_excluded_series(self):
                self.assertTrue(is_excluded_series({"sub_category": "로판"}))
                self.assertTrue(is_excluded_series({"sub_category": "로맨스"}))
                self.assertFalse(is_excluded_series({"sub_category": "판타지"}))
                self.assertFalse(is_excluded_series({}))

            # --- extract_episodes ---

            def test_extract_episodes(self):
                data = {"result": {"list": [{"item": {"order_value": 1}}, {"x": 1}]}}
                self.assertEqual(extract_episodes(data), [{"order_value": 1}])

            def test_extract_episodes_empty(self):
                self.assertEqual(extract_episodes({}), [])

            # --- compose_description ---

            def test_compose_description_basic(self):
                series = {
                    "title": "Toon",
                    "sub_category": "무협",
                    "authors": "A,B",
                    "description": "story",
                }
                out = compose_description(
                    series, "http://l.test/1", LOGIN_REQUIRED, "http://img.test/x.jpg"
                )
                self.assertIn("<div>Toon</div>", out)
                self.assertIn("<div>로그인 열람 필수</div>", out)
                self.assertIn("<div>무협</div>", out)
                self.assertIn("<div>A,B</div>", out)
                self.assertIn("<div>story</div>", out)
                self.assertIn("<img src='http://img.test/x.jpg'>", out)

            def test_compose_description_omits_empty_status_and_cover(self):
                out = compose_description({"title": "T"}, "l")
                self.assertNotIn("열람", out)
                self.assertNotIn("<img", out)

            def test_compose_description_truncates_description(self):
                out = compose_description({"title": "T", "description": "x" * 300}, "l")
                self.assertIn("<div>" + "x" * 200 + "</div>", out)

            # --- download_with_retry ---

            class _FakeCrawler:
                def __init__(self, results):
                    self.results = list(results)
                    self.calls = 0

                def run(self, url, download_file=None):
                    self.calls += 1
                    return self.results.pop(0)

            def _retry(self, results):
                crawler = self._FakeCrawler(results)
                with mock.patch("time.sleep") as sleep:
                    ok = download_with_retry(crawler, "u", Path("p"))
                return ok, crawler.calls, sleep.call_count

            def test_download_succeeds_first_try(self):
                self.assertEqual(self._retry([("ok", None, 200)]), (True, 1, 0))

            def test_download_succeeds_after_one_failure(self):
                fail = (None, "err", 404)
                self.assertEqual(self._retry([fail, ("ok", None, 200)]), (True, 2, 1))

            def test_download_succeeds_after_two_failures(self):
                fail = (None, "err", 404)
                self.assertEqual(
                    self._retry([fail, fail, ("ok", None, 200)]), (True, 3, 2)
                )

            def test_download_gives_up_after_two_retries(self):
                fail = (None, "err", 404)
                self.assertEqual(self._retry([fail, fail, fail]), (False, 3, 2))

        sys.exit(unittest.main())
    else:
        sys.exit(main())
