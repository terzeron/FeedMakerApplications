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

            # --- end-to-end with real sampled pipeline data ---
            # 입력: crawler.py(--render-js=true)로 t3.xtoon365.com 에피소드(chapter/1474756) 원본 HTML 중
            #       파서가 act하는 data-original 이미지 라인 2개만 샘플링(element_class 없음 → raw 사용).
            # 기대 출력: 동일 입력을 'post_process_xtoon.py'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '<img class="lazy-read" data-original="https://cdn.xtoon33.com/toon/2026/74af5d66d4aafe6dad10fb6c340f113bd88c2e06.jpg" src="/template/pc/default/images/bg_detail.png" alt="251화최신업데이트 무료웹툰 성인웹툰">',
                '<img class="lazy-read" data-original="https://cdn.xtoon33.com/toon/2026/4f0d83751a471773d1f2f3c92bf644068f6ed202.jpg" src="/template/pc/default/images/bg_detail.png" alt="251화최신업데이트 무료웹툰 성인웹툰">',
            ]

            def test_real_sample_end_to_end(self):
                self.assertEqual(
                    extract_image_tags(self.REAL_SAMPLE_LINES),
                    [
                        "<img src='https://cdn.xtoon33.com/toon/2026/74af5d66d4aafe6dad10fb6c340f113bd88c2e06.jpg' />",
                        "<img src='https://cdn.xtoon33.com/toon/2026/4f0d83751a471773d1f2f3c92bf644068f6ed202.jpg' />",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
