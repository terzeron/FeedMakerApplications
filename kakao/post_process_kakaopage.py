#!/usr/bin/env python

import os
import sys
import re
import json
import getopt
import urllib.request
from typing import List, Optional
from bin.feed_maker_util import header_str


VIEWER_DATA_URL = "https://bff-page.kakao.com/api/gateway/api/v1/viewer/data?series_id=%s&product_id=%s"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


def parse_item_url(url: str) -> Optional[tuple]:
    """뷰어 URL에서 (series_id, product_id)를 뽑는다."""
    m = re.search(r"/content/(\d+)/viewer/(\d+)", url)
    if not m:
        return None
    return m.group(1), m.group(2)


def is_free_item(json_data: dict) -> bool:
    """viewer/data의 item.is_free가 True인 무료 회차인지 확인한다."""
    return bool(json_data.get("item", {}).get("is_free"))


def extract_image_urls(json_data: dict) -> List[str]:
    """viewer/data 응답에서 이미지 URL을 no 순서대로 뽑는다."""
    files = (
        json_data.get("viewer_data", {}).get("imageDownloadData", {}).get("files", [])
    )
    return [
        f["secureUrl"]
        for f in sorted(files, key=lambda f: f.get("no", 0))
        if f.get("secureUrl")
    ]


def render_html(image_urls: List[str]) -> str:
    """이미지 URL 목록을 피드 본문 HTML로 만든다."""
    body = "".join("<img src='%s'/>\n" % url for url in image_urls)
    return header_str + "<div>\n" + body + "</div>\n"


def fetch_viewer_data(series_id: str, product_id: str) -> dict:
    req = urllib.request.Request(
        VIEWER_DATA_URL % (series_id, product_id),
        headers={"User-Agent": USER_AGENT, "Referer": "https://page.kakao.com/"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    _, args = getopt.getopt(sys.argv[1:], "f:")
    for _ in sys.stdin:  # 뷰어 HTML은 쓰지 않고 API 결과만 쓴다.
        pass
    if not args:
        return -1
    ids = parse_item_url(args[0])
    if not ids:
        return -1
    data = fetch_viewer_data(*ids)
    if not is_free_item(data):
        return -1
    image_urls = extract_image_urls(data)
    if not image_urls:
        return -1
    print(render_html(image_urls))
    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcess(unittest.TestCase):
            def test_parse_item_url(self):
                self.assertEqual(
                    parse_item_url(
                        "https://page.kakao.com/content/60105861/viewer/70352693"
                    ),
                    ("60105861", "70352693"),
                )
                self.assertIsNone(parse_item_url("https://example.com/x"))

            def test_extract_image_urls_sorted(self):
                data = {
                    "viewer_data": {
                        "imageDownloadData": {
                            "files": [
                                {"no": 2, "secureUrl": "u2"},
                                {"no": 1, "secureUrl": "u1"},
                                {"no": 3},
                            ]
                        }
                    }
                }
                self.assertEqual(extract_image_urls(data), ["u1", "u2"])

            def test_is_free_item(self):
                self.assertTrue(is_free_item({"item": {"is_free": True}}))
                self.assertFalse(is_free_item({"item": {"is_free": False}}))
                self.assertFalse(is_free_item({}))

            def test_extract_image_urls_empty(self):
                self.assertEqual(extract_image_urls({}), [])

            def test_render_html_keeps_raw_ampersand(self):
                # download_image.py는 &amp;를 풀지 않으므로 서명 URL의 &를 그대로 둔다.
                self.assertIn("<img src='a?x=1&y=2'/>", render_html(["a?x=1&y=2"]))

        sys.exit(unittest.main())
    else:
        sys.exit(main())
