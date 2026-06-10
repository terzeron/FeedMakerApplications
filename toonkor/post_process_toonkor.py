#!/usr/bin/env python

import os
import sys
import re
import base64
from typing import List
from bs4 import BeautifulSoup
from bin.feed_maker_util import IO, URL, header_str


def decode_toon_images(b64_str: str, url_prefix: str) -> List[str]:
    """base64로 인코딩된 tnimg HTML을 디코드해 img 태그 목록을 만든다."""
    html = base64.b64decode(b64_str).decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")
    result: List[str] = []
    for img in soup.find_all("img"):
        img_url = URL.concatenate_url(url_prefix, img["src"])
        result.append(f"<img src='{img_url}' />")
    return result


def main():
    url_prefix = ""
    state = 0

    for line in IO.read_stdin_as_line_list():
        if state == 0:
            m = re.search(
                r'<meta property="og:url" content="(?P<url_prefix>http[^"]+)"', line
            )
            if m:
                url_prefix = m.group("url_prefix")
                print(header_str)
                state = 1
        elif state == 1:
            m = re.search(r"var tnimg\s*=\s*\x27(?P<str>[^\x27]+)\x27", line)
            if m:
                for tag in decode_toon_images(m.group("str"), url_prefix):
                    print(tag)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest
        from unittest.mock import patch

        def _b64(html: str) -> str:
            return base64.b64encode(html.encode("utf-8")).decode("ascii")

        class TestPostProcessToonkor(unittest.TestCase):
            def test_decode_toon_images_basic(self):
                b64 = _b64('<img src="/a.jpg"><img src="/b.jpg">')
                with patch(
                    "__main__.URL.concatenate_url",
                    side_effect=lambda base, rel: base + rel,
                ):
                    result = decode_toon_images(b64, "https://t.test")
                self.assertEqual(
                    result,
                    [
                        "<img src='https://t.test/a.jpg' />",
                        "<img src='https://t.test/b.jpg' />",
                    ],
                )

            def test_decode_toon_images_no_img(self):
                with patch(
                    "__main__.URL.concatenate_url", side_effect=lambda b, r: b + r
                ):
                    self.assertEqual(decode_toon_images(_b64("<p>none</p>"), "x"), [])

            def test_decode_toon_images_single(self):
                b64 = _b64('<img src="x.png">')
                with patch(
                    "__main__.URL.concatenate_url", side_effect=lambda b, r: b + r
                ):
                    self.assertEqual(
                        decode_toon_images(b64, "p/"), ["<img src='p/x.png' />"]
                    )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
