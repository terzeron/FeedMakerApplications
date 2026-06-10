#!/usr/bin/env python


import os
import sys
import re
import json
from typing import List
from bin.feed_maker_util import IO
from bin.crawler import Crawler


def filter_input_lines(line_list: List[str]) -> List[str]:
    """'<img src'로 시작하는 줄을 제외하고 rstrip한 줄 목록을 반환."""
    result: List[str] = []
    for line in line_list:
        line = line.rstrip()
        if not re.search(r"^<img src", line):
            result.append(line)
    return result


def extract_image_tags(content: dict) -> List[str]:
    """뷰어 JSON(data[].url)에서 VodPlayer.swf를 뺀 이미지 img 태그 목록을 만든다."""
    result: List[str] = []
    if "data" in content and content["data"]:
        for item in content["data"]:
            if "url" in item:
                img_url = item["url"]
                if re.search(r"VodPlayer\.swf", img_url):
                    continue
                result.append("<img src='%s' width='100%%'/>" % (img_url))
    return result


def main():
    for line in filter_input_lines(IO.read_stdin_as_line_list()):
        print(line)

    post_link = sys.argv[1]
    m = re.search(
        r"http://cartoon\.media\.daum\.net/(?P<mobile>m/)?webtoon/viewer/(?P<episode_id>\d+)$",
        post_link,
    )
    if m:
        episode_id = m.group("episode_id")
        url = "http://webtoon.daum.net/data/pc/webtoon/viewer_images/" + episode_id
        crawler = Crawler()
        result, _ = crawler.run(url)
        if not result:
            print("can't download the page html from '%s'" % (url))
            sys.exit(-1)
        try:
            content = json.loads(result)
        except json.decoder.JSONDecodeError:
            raise json.decoder.JSONDecodeError

        for img_tag in extract_image_tags(content):
            print(img_tag)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessDaumwebtoon(unittest.TestCase):
            # --- filter_input_lines ---

            def test_filter_input_lines_drops_img_src_lines(self):
                lines = ["<p>keep</p>", "<img src='a.jpg'/>", "text"]
                self.assertEqual(filter_input_lines(lines), ["<p>keep</p>", "text"])

            def test_filter_input_lines_rstrips(self):
                self.assertEqual(filter_input_lines(["hello   \n"]), ["hello"])

            def test_filter_input_lines_keeps_img_not_at_start(self):
                self.assertEqual(
                    filter_input_lines(["  <img src='a'/>"]), ["  <img src='a'/>"]
                )

            def test_filter_input_lines_empty(self):
                self.assertEqual(filter_input_lines([]), [])

            # --- extract_image_tags ---

            def test_extract_image_tags_basic(self):
                content = {"data": [{"url": "http://a.test/1.jpg"}]}
                self.assertEqual(
                    extract_image_tags(content),
                    ["<img src='http://a.test/1.jpg' width='100%'/>"],
                )

            def test_extract_image_tags_skips_vodplayer(self):
                content = {
                    "data": [
                        {"url": "http://a.test/VodPlayer.swf"},
                        {"url": "http://a.test/2.jpg"},
                    ]
                }
                self.assertEqual(
                    extract_image_tags(content),
                    ["<img src='http://a.test/2.jpg' width='100%'/>"],
                )

            def test_extract_image_tags_no_data(self):
                self.assertEqual(extract_image_tags({}), [])

            def test_extract_image_tags_empty_data(self):
                self.assertEqual(extract_image_tags({"data": []}), [])

            def test_extract_image_tags_item_without_url(self):
                self.assertEqual(extract_image_tags({"data": [{"x": 1}]}), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
