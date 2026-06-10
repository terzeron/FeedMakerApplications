#!/usr/bin/env python

import os
import sys
import re
from typing import List
from bin.feed_maker_util import IO


def extract_clip_content(line_list: List[str]) -> List[str]:
    """__clipContent script 태그 안쪽의 줄들만 추출한다."""
    state = 0
    result: List[str] = []
    for line in line_list:
        if state == 0:
            if re.search(r'<script[^>]*id="__clipContent">', line):
                state = 1
        elif state == 1:
            if re.search(r"</script>", line):
                state = 0
            else:
                result.append(line)
    return result


def main():
    line_list = IO.read_stdin_as_line_list()
    for line in extract_clip_content(line_list):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessNaverpost(unittest.TestCase):
            def test_extract_clip_content_basic(self):
                lines = [
                    "<html>",
                    '<script type="text/x" id="__clipContent">',
                    "<p>body</p>",
                    "</script>",
                    "<footer>",
                ]
                self.assertEqual(extract_clip_content(lines), ["<p>body</p>"])

            def test_extract_clip_content_multiple_lines(self):
                lines = [
                    '<script id="__clipContent">',
                    "line1",
                    "line2",
                    "</script>",
                ]
                self.assertEqual(extract_clip_content(lines), ["line1", "line2"])

            def test_extract_clip_content_no_clip(self):
                self.assertEqual(extract_clip_content(["<p>nope</p>"]), [])

            def test_extract_clip_content_empty(self):
                self.assertEqual(extract_clip_content([]), [])

            def test_extract_clip_content_ignores_after_close(self):
                lines = [
                    '<script id="__clipContent">',
                    "inside",
                    "</script>",
                    "outside",
                ]
                self.assertEqual(extract_clip_content(lines), ["inside"])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
