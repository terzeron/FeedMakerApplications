#!/usr/bin/env python

import os
import sys
import re
from typing import List
from bin.feed_maker_util import IO


def extract_image_tags(line_list: List[str]) -> List[str]:
    """각 줄의 data-original 이미지 URL을 뽑아 img 태그 목록으로 변환한다."""
    result: List[str] = []
    for line in line_list:
        m = re.search(r'<img[^>]*data-original="(?P<img_url>[^"]+)"', line)
        if m:
            img_url = m.group("img_url")
            result.append(f"<img src='{img_url}' />")
    return result


def main():
    for tag in extract_image_tags(IO.read_stdin_as_line_list()):
        print(tag)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessXtoon(unittest.TestCase):
            def test_extract_image_tags_basic(self):
                lines = ['<img class="lazy" data-original="http://x.test/1.jpg">']
                self.assertEqual(
                    extract_image_tags(lines), ["<img src='http://x.test/1.jpg' />"]
                )

            def test_extract_image_tags_multiple(self):
                lines = [
                    '<img data-original="a.jpg">',
                    "<p>noise</p>",
                    '<img data-original="b.jpg">',
                ]
                self.assertEqual(
                    extract_image_tags(lines),
                    ["<img src='a.jpg' />", "<img src='b.jpg' />"],
                )

            def test_extract_image_tags_ignores_plain_img(self):
                self.assertEqual(extract_image_tags(['<img src="a.jpg">']), [])

            def test_extract_image_tags_no_match(self):
                self.assertEqual(extract_image_tags(["<div>nothing</div>"]), [])

            def test_extract_image_tags_empty(self):
                self.assertEqual(extract_image_tags([]), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
