#!/usr/bin/env python

import os
import sys
import re
from typing import List
from bin.feed_maker_util import IO


def extract_image_tags(line_list: List[str]) -> List[str]:
    """각 줄의 class="reader-page" 이미지 src를 뽑아 img 태그 목록으로 변환한다."""
    result: List[str] = []
    for line in line_list:
        m = re.search(
            r'<img(?=[^>]*\bclass="reader-page")[^>]*\bsrc="(?P<img_url>[^"]+)"', line
        )
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
                lines = ['<img src="http://x.test/1.jpg" class="reader-page">']
                self.assertEqual(
                    extract_image_tags(lines), ["<img src='http://x.test/1.jpg' />"]
                )

            def test_extract_image_tags_multiple(self):
                lines = [
                    '<img src="a.jpg" class="reader-page">',
                    "<p>noise</p>",
                    '<img src="b.jpg" class="reader-page">',
                ]
                self.assertEqual(
                    extract_image_tags(lines),
                    ["<img src='a.jpg' />", "<img src='b.jpg' />"],
                )

            def test_extract_image_tags_ignores_non_reader_page_img(self):
                self.assertEqual(
                    extract_image_tags(['<img src="ad.png" class="ads-banner">']), []
                )

            def test_extract_image_tags_no_match(self):
                self.assertEqual(extract_image_tags(["<div>nothing</div>"]), [])

            def test_extract_image_tags_empty(self):
                self.assertEqual(extract_image_tags([]), [])

            # --- end-to-end with real sampled pipeline data ---
            # 입력: crawler.py(--render-js=true)로 newxtoon1.com 에피소드(comics/9818/chapters/801302) 렌더링 HTML 중
            #       파서가 매칭하는 class="reader-page" 이미지 라인 2개만 샘플링.
            #       (2026-09 xtoon 사이트가 t3.xtoon365.com에서 newxtoon1.com으로 리뉴얼되며 마크업이 전면 교체됨:
            #        data-original 속성 대신 src에 실제 이미지가 바로 들어있고, render_js로 렌더링해야 img 태그가 나타남)
            # 기대 출력: 동일 입력을 'post_process_xtoon.py'로 직접 실행해 캡처한 결과.
            REAL_SAMPLE_LINES = [
                '<img src="https://user281.quicksharefiles.top/toon/841632/20e7a2326285dfabc9d217a832b7aabbc5a590a2.jpg" alt="사마쌍협 54화(시즌 1 완결) 1번째 이미지" width="480" height="623" loading="eager" class="reader-page" data-reader-image="">',
                '<img src="https://user281.quicksharefiles.top/toon/841632/fc562eaf3b425f122c0aa4a26948b4d86d270473.jpg" alt="사마쌍협 54화(시즌 1 완결) 2번째 이미지" width="480" height="623" loading="eager" class="reader-page" data-reader-image="">',
            ]

            def test_real_sample_end_to_end(self):
                self.assertEqual(
                    extract_image_tags(self.REAL_SAMPLE_LINES),
                    [
                        "<img src='https://user281.quicksharefiles.top/toon/841632/20e7a2326285dfabc9d217a832b7aabbc5a590a2.jpg' />",
                        "<img src='https://user281.quicksharefiles.top/toon/841632/fc562eaf3b425f122c0aa4a26948b4d86d270473.jpg' />",
                    ],
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
