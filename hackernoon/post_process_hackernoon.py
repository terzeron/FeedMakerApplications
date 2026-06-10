#!/usr/bin/env python


import os
import sys
import re
import json
from typing import List
from bin.feed_maker_util import IO, header_str


def extract_contents(content: str) -> List[str]:
    """페이지의 <script> JSON에서 props.pageProps.data.markup(없으면 parsed) 본문을 모은다."""
    result: List[str] = []
    matches = re.findall(r"<script[^>]*>(?P<json_str>{.+?})</script>", content)
    for match in matches:
        data = json.loads(match)
        if "props" in data:
            props = data["props"]
            if "pageProps" in props:
                page_props = props["pageProps"]
                if "data" in page_props:
                    d = page_props["data"]
                    if "markup" in d and d["markup"]:
                        result.append(d["markup"])
                    elif "parsed" in d and d["parsed"]:
                        result.append(d["parsed"])
    return result


def main():
    print(header_str)

    for content in extract_contents(IO.read_stdin()):
        print(content)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        def _script(data: dict) -> str:
            return '<script type="application/json">' + json.dumps(data) + "</script>"

        class TestPostProcessHackernoon(unittest.TestCase):
            def test_extract_contents_markup(self):
                content = _script(
                    {"props": {"pageProps": {"data": {"markup": "<p>hi</p>"}}}}
                )
                self.assertEqual(extract_contents(content), ["<p>hi</p>"])

            def test_extract_contents_parsed_fallback(self):
                content = _script(
                    {"props": {"pageProps": {"data": {"parsed": "parsed body"}}}}
                )
                self.assertEqual(extract_contents(content), ["parsed body"])

            def test_extract_contents_markup_preferred_over_parsed(self):
                content = _script(
                    {"props": {"pageProps": {"data": {"markup": "M", "parsed": "P"}}}}
                )
                self.assertEqual(extract_contents(content), ["M"])

            def test_extract_contents_empty_markup_falls_back(self):
                content = _script(
                    {"props": {"pageProps": {"data": {"markup": "", "parsed": "P"}}}}
                )
                self.assertEqual(extract_contents(content), ["P"])

            def test_extract_contents_no_props(self):
                self.assertEqual(extract_contents(_script({"other": 1})), [])

            def test_extract_contents_no_script(self):
                self.assertEqual(extract_contents("<div>no script here</div>"), [])

            def test_extract_contents_multiple_scripts(self):
                content = _script(
                    {"props": {"pageProps": {"data": {"markup": "A"}}}}
                ) + _script({"props": {"pageProps": {"data": {"markup": "B"}}}})
                self.assertEqual(extract_contents(content), ["A", "B"])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
