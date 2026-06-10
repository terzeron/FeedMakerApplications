#!/usr/bin/env python


import os
import sys
import re
from bin.feed_maker_util import IO


def convert_line(line: str) -> str:
    """blacktoon 이미지 URL을 정규 도메인으로 바꾸고, img 태그의 공백/대괄호를 percent-encoding 한다."""
    line = re.sub(
        r"https://blacktoon\d+.com/webtoons/\d+/", "https://img.blacktoonimg.com/", line
    )
    if re.search(r"<img src=", line):
        line = re.sub(r" ", "%20", line)
        line = re.sub(r"<img%20src", "<img src", line)
    line = re.sub(r"\[", "%5B", line)
    line = re.sub(r"\]", "%5D", line)
    return line


def main():
    for line in IO.read_stdin_as_line_list():
        print(convert_line(line), end="")


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestConvertBlacktoonUrl(unittest.TestCase):
            def test_rewrites_image_domain(self):
                self.assertEqual(
                    convert_line("see https://blacktoon123.com/webtoons/45/a.jpg"),
                    "see https://img.blacktoonimg.com/a.jpg",
                )

            def test_encodes_spaces_only_in_img_tag(self):
                self.assertEqual(
                    convert_line('<img src="http://a.test/b c.jpg">'),
                    '<img src="http://a.test/b%20c.jpg">',
                )

            def test_keeps_img_src_keyword_unencoded(self):
                # 공백 치환 후에도 '<img src' 키워드는 복원된다
                out = convert_line('<img src="x y">')
                self.assertTrue(out.startswith("<img src="))

            def test_does_not_encode_spaces_outside_img_tag(self):
                self.assertEqual(convert_line("a b c"), "a b c")

            def test_encodes_brackets(self):
                self.assertEqual(convert_line("a[b]c"), "a%5Bb%5Dc")

            def test_plain_line_unchanged(self):
                self.assertEqual(convert_line("plain text\n"), "plain text\n")

        sys.exit(unittest.main())
    else:
        sys.exit(main())
