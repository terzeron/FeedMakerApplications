#!/usr/bin/env python

import os
import sys
import json
import urllib.parse
import logging
import logging.config
import getopt
from pathlib import Path
from bin.feed_maker_util import Config
from bin.crawler import Crawler, Method


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger(__name__)


IMG_URL_PREFIX = "https://page-edge.kakao.com/sdownload/resource?kid="


def extract_image_tags(data: dict, img_url_prefix: str = IMG_URL_PREFIX) -> list:
    """다운로드 응답(downloadData.members.files)에서 이미지 img 태그 목록을 만든다."""
    result = []
    if (
        "downloadData" in data
        and "members" in data["downloadData"]
        and "files" in data["downloadData"]["members"]
    ):
        for file in data["downloadData"]["members"]["files"]:
            img_url = img_url_prefix + file["secureUrl"]
            result.append("<img src='%s'>" % img_url)
    return result


def main() -> int:
    feed_dir_path = Path.cwd()
    img_url_prefix = "https://page-edge.kakao.com/sdownload/resource?kid="

    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)

    if not feed_dir_path or not feed_dir_path.is_dir():
        LOGGER.error(f"can't find such a directory '{feed_dir_path}'")
        return -1

    for _ in sys.stdin:
        pass

    page_url = args[0]
    parsed_url = urllib.parse.urlparse(page_url)
    qs = urllib.parse.parse_qs(parsed_url.query)
    product_id = qs["productId"][0]
    LOGGER.debug(product_id)

    config = Config(feed_dir_path=feed_dir_path)
    extraction_conf = config.get_extraction_configs()
    user_agent_str = extraction_conf["user_agent"]

    api_url = "https://api2-page.kakao.com/api/v1/inven/get_download_data/web"
    header = {"User-Agent": user_agent_str}
    data = {"productId": product_id, "deviceId": "07fb8773b324c189df8d99dc6c296838"}
    LOGGER.debug(api_url)
    LOGGER.debug(header)
    LOGGER.debug(data)
    crawler = Crawler(dir_path=feed_dir_path, render_js=False, method=Method.POST)
    result, error, _ = crawler.run(api_url, data)
    if error:
        LOGGER.error(f"Error: can't get data from '{api_url}'")
        return -1
    data = json.loads(result)

    for img_tag in extract_image_tags(data, img_url_prefix):
        print(img_tag)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessKakaopage(unittest.TestCase):
            def test_extract_image_tags_basic(self):
                data = {
                    "downloadData": {
                        "members": {
                            "files": [{"secureUrl": "abc"}, {"secureUrl": "def"}]
                        }
                    }
                }
                self.assertEqual(
                    extract_image_tags(data),
                    [
                        "<img src='https://page-edge.kakao.com/sdownload/resource?kid=abc'>",
                        "<img src='https://page-edge.kakao.com/sdownload/resource?kid=def'>",
                    ],
                )

            def test_extract_image_tags_custom_prefix(self):
                data = {"downloadData": {"members": {"files": [{"secureUrl": "x"}]}}}
                self.assertEqual(
                    extract_image_tags(data, "http://p/"), ["<img src='http://p/x'>"]
                )

            def test_extract_image_tags_no_download_data(self):
                self.assertEqual(extract_image_tags({}), [])

            def test_extract_image_tags_no_files(self):
                self.assertEqual(
                    extract_image_tags({"downloadData": {"members": {}}}), []
                )

            def test_extract_image_tags_empty_files(self):
                self.assertEqual(
                    extract_image_tags({"downloadData": {"members": {"files": []}}}), []
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
