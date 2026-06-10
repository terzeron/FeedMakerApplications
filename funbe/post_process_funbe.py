#!/usr/bin/env python

import os
import sys
import re
import base64
from typing import List
from bs4 import BeautifulSoup
from bin.feed_maker_util import IO, URL


def decode_toon_images(b64_str: str, url_prefix: str) -> List[str]:
    """base64로 인코딩된 toon_img HTML을 디코드해 img 태그 목록을 만든다."""
    html = base64.b64decode(b64_str).decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    result: List[str] = []
    for img in soup.find_all("img"):
        img_url = URL.concatenate_url(url_prefix, img["src"])
        result.append(f"<img src='{img_url}' />")
    return result


def extract_image_tags(line_list: List[str]) -> List[str]:
    """og:url로 prefix를 잡은 뒤 toon_img base64를 디코드해 img 태그 목록을 만든다."""
    url_prefix = ""
    state = 0
    result: List[str] = []
    for line in line_list:
        if state == 0:
            m = re.search(
                r'<meta property="og:url" content="(?P<url_prefix>http[^"]+)"', line
            )
            if m:
                url_prefix = m.group("url_prefix")
                state = 1
        elif state == 1:
            m = re.search(r"var toon_img\s*=\s*\x27(?P<str>[^\x27]+)\x27", line)
            if m:
                result.extend(decode_toon_images(m.group("str"), url_prefix))
    return result


def main():
    for tag in extract_image_tags(IO.read_stdin_as_line_list()):
        print(tag)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest
        from unittest.mock import patch

        def _b64(html: str) -> str:
            return base64.b64encode(html.encode("utf-8")).decode("ascii")

        class TestPostProcessFunbe(unittest.TestCase):
            # --- decode_toon_images ---

            def test_decode_toon_images_basic(self):
                b64 = _b64('<img src="/a.jpg"><img src="/b.jpg">')
                with patch(
                    "__main__.URL.concatenate_url",
                    side_effect=lambda base, rel: base + rel,
                ):
                    result = decode_toon_images(b64, "https://f.test")
                self.assertEqual(
                    result,
                    [
                        "<img src='https://f.test/a.jpg' />",
                        "<img src='https://f.test/b.jpg' />",
                    ],
                )

            def test_decode_toon_images_no_img(self):
                with patch(
                    "__main__.URL.concatenate_url", side_effect=lambda b, r: b + r
                ):
                    self.assertEqual(decode_toon_images(_b64("<p>none</p>"), "x"), [])

            # --- extract_image_tags ---

            def test_extract_image_tags_basic(self):
                b64 = _b64('<img src="/a.jpg">')
                lines = [
                    '<meta property="og:url" content="https://f.test/ep/1">',
                    f"var toon_img = '{b64}'",
                ]
                with patch(
                    "__main__.URL.concatenate_url", side_effect=lambda b, r: b + r
                ):
                    result = extract_image_tags(lines)
                self.assertEqual(result, ["<img src='https://f.test/ep/1/a.jpg' />"])

            def test_extract_image_tags_requires_og_url(self):
                b64 = _b64('<img src="/a.jpg">')
                with patch(
                    "__main__.URL.concatenate_url", side_effect=lambda b, r: b + r
                ):
                    self.assertEqual(
                        extract_image_tags([f"var toon_img = '{b64}'"]), []
                    )

            def test_extract_image_tags_empty(self):
                self.assertEqual(extract_image_tags([]), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
