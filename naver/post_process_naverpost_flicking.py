#!/usr/bin/env python

import os
import sys
import re
import json
from typing import Optional, Tuple
from bin.feed_maker_util import IO


def parse_volume_member(arg: str) -> Tuple[Optional[int], Optional[int]]:
    """인자 문자열에서 (volumeNo, memberNo)를 추출(없으면 (None, None))."""
    m = re.search(r"volumeNo=(?P<volumeNo>\d+)&memberNo=(?P<memberNo>\d+)", arg)
    if m:
        return int(m.group("volumeNo")), int(m.group("memberNo"))
    return None, None


def clean_input_line(line: str) -> str:
    """줄 끝 공백과 제어문자(\\x01, \\x08)를 제거한다."""
    line = line.rstrip()
    line = re.sub(r"[\x01\x08]", "", line, re.LOCALE)
    return line


def transform_clip_content(clip_content: str) -> str:
    """clipContent의 이미지 placeholder를 실제 URL로 바꾸고 toast_flick 이미지를 제거한다."""
    clip_content = re.sub(
        r'src="{{{[^\|]*\|/([^\|]+)\|\d+|\d+}}}"',
        r'src="http://post.phinf.naver.net/\1"',
        clip_content,
    )
    clip_content = re.sub(
        r"<img src=\'http://static.post.naver.net/image/im/end/toast_flick.png\'/>",
        "",
        clip_content,
    )
    return clip_content


def main():
    volumeNo, memberNo = parse_volume_member(sys.argv[1])

    lineList = IO.read_stdin_as_line_list()
    for line in lineList:
        print(clean_input_line(line))

    failureCount = 0
    link_prefix = (
        "http://m.post.naver.com/viewer/clipContentJson.naver?volumeNo=%d&memberNo=%d&clipNo="
        % (volumeNo, memberNo)
    )
    for clipNo in range(30):
        link = link_prefix + str(clipNo)
        cmd = 'wget.sh "%s" utf8' % (link)
        (result, error) = feed_maker_util.exec_cmd(cmd)
        if error or re.search(r'"notExistClip"', result):
            failureCount = failureCount + 1
            if failureCount > 2:
                break
        else:
            clipContent = json.loads(result)["clipContent"]
            print(transform_clip_content(clipContent))


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessNaverpostFlicking(unittest.TestCase):
            # --- parse_volume_member ---

            def test_parse_volume_member_basic(self):
                self.assertEqual(
                    parse_volume_member("x?volumeNo=12&memberNo=34&y"), (12, 34)
                )

            def test_parse_volume_member_no_match(self):
                self.assertEqual(parse_volume_member("nothing here"), (None, None))

            # --- clean_input_line ---

            def test_clean_input_line_rstrip(self):
                self.assertEqual(clean_input_line("hello   "), "hello")

            def test_clean_input_line_removes_control_chars(self):
                self.assertEqual(clean_input_line("a\x01b\x08c"), "abc")

            def test_clean_input_line_plain(self):
                self.assertEqual(clean_input_line("plain"), "plain")

            # --- transform_clip_content ---

            def test_transform_clip_content_removes_toast_flick(self):
                content = "before<img src='http://static.post.naver.net/image/im/end/toast_flick.png'/>after"
                self.assertEqual(transform_clip_content(content), "beforeafter")

            def test_transform_clip_content_passthrough(self):
                self.assertEqual(transform_clip_content("<p>plain</p>"), "<p>plain</p>")

        sys.exit(unittest.main())
    else:
        sys.exit(main())
