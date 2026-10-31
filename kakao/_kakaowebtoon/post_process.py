#!/usr/bin/env python

import sys
import os
import re
import json
import getopt
import subprocess
import logging
import logging.config
from pathlib import Path
from bin.feed_maker_util import IO, URL, header_str, Env
from bin.feed_maker import FeedMaker
from bin.crawler import Crawler


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def compose_description(item, link) -> str:
    description = "<div>\n"
    description += "    <div>%s</div>\n" % item["title"]
    description += "    <div>%s</div>\n" % item.get("genre", "")
    description += "    <div>%s</div>\n" % item.get("synopsis", "")[:200]
    description += "    <div><a href='%s'>%s</a></div>\n" % (link, link)
    if item.get("mergedImage"):
        description += "    <div><img src='%s'></div>\n" % (item["mergedImage"])
    description += "</div>\n"
    return description


def extract_next_data(content: str):
    """HTML에서 __NEXT_DATA__ script 태그의 JSON 문자열을 추출(없으면 None)."""
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', content
    )
    if not match:
        return None
    return match.group(1)


def select_content_item(content_map: dict, item_url: str):
    """contentMap에서 URL 끝의 ID로 content를 찾고, 없으면 첫 번째 항목을 반환."""
    content_id = None
    if item_url:
        id_match = re.search(r"/(\d+)$", item_url)
        if id_match:
            content_id = id_match.group(1)

    if content_id and content_id in content_map:
        return content_map[content_id]
    if content_id and int(content_id) in content_map:
        return content_map[int(content_id)]
    return next(iter(content_map.values()))


def _download_with_retry(
    crawler: Crawler, url: str, file_path: Path, label: str
) -> bool:
    """이미지 다운로드를 시도하고, 실패 시 5초 후 1회 재시도한다."""
    import time

    result, error, _ = crawler.run(url, download_file=file_path)
    if result and not error:
        return True
    LOGGER.warning(
        "failed to download %s image '%s' (%s), retrying...", label, url, error
    )
    time.sleep(5)
    result, error, _ = crawler.run(url, download_file=file_path)
    if result and not error:
        return True
    LOGGER.warning(
        "can't download %s image '%s' to '%s', %s", label, url, file_path, error
    )
    return False


def download_and_merge(
    crawler: Crawler,
    download_dir_path: Path,
    background_image_url: str,
    foreground_image_url: str,
    item_id: str,
) -> str:
    background_image_path = download_dir_path / (item_id + "_background.webp")
    foreground_image_path = download_dir_path / (item_id + "_foreground.png")
    merged_image_path = download_dir_path / (item_id + ".png")

    if not background_image_path.is_file() or background_image_path.stat().st_size == 0:
        if not _download_with_retry(
            crawler, background_image_url, background_image_path, "background"
        ):
            return ""

    if not foreground_image_path.is_file() or foreground_image_path.stat().st_size == 0:
        if not _download_with_retry(
            crawler, foreground_image_url, foreground_image_path, "foreground"
        ):
            return ""

    if not merged_image_path.is_file() or merged_image_path.stat().st_size == 0:
        cropped_background_image_path = download_dir_path / (
            item_id + "_cropped_background.webp"
        )
        result = subprocess.run(
            [
                "convert",
                str(background_image_path),
                "-crop",
                "750x824+0+0",
                "+repage",
                str(cropped_background_image_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.returncode != 0:
            LOGGER.error(
                "can't merge images '%s' and '%s' to '%s'",
                background_image_path,
                cropped_background_image_path,
                merged_image_path,
            )
            return ""
        result = subprocess.run(
            [
                "convert",
                str(cropped_background_image_path),
                str(foreground_image_path),
                "-gravity",
                "south",
                "-composite",
                str(merged_image_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        if result.returncode != 0:
            LOGGER.error(
                "can't merge images '%s' and '%s' to '%s'",
                cropped_background_image_path,
                foreground_image_path,
                merged_image_path,
            )
            return ""

    return (
        Env.get("WEB_SERVICE_IMAGE_URL_PREFIX")
        + "/kakaowebtoon/"
        + merged_image_path.name
    )


def main() -> int:
    link_prefix = "https://webtoon.kakao.com/content"
    feed_dir_path = Path.cwd()
    item_url = ""

    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)

    if args:
        item_url = args[0]

    crawler = Crawler()
    download_dir_path = Path(Env.get("WEB_SERVICE_IMAGE_DIR_PREFIX")) / "kakaowebtoon"

    content = IO.read_stdin()

    # __NEXT_DATA__ script 태그에서 JSON 추출
    json_content = extract_next_data(content)
    if not json_content:
        LOGGER.error("can't find __NEXT_DATA__ in HTML")
        del crawler
        return -1

    try:
        json_data = json.loads(json_content)
    except json.JSONDecodeError as e:
        LOGGER.error("can't parse JSON: %s", e)
        del crawler
        return -1

    # props.initialState.content.contentMap 에서 content 추출
    item = None
    try:
        content_map = json_data["props"]["initialState"]["content"]["contentMap"]
        # contentMap에서 URL의 ID로 찾고, 없으면 첫 번째 항목 사용
        item = select_content_item(content_map, item_url)
    except (KeyError, TypeError) as e:
        LOGGER.error("can't find content in JSON structure: %s", e)
        del crawler
        return -1

    if not item or "title" not in item:
        LOGGER.error("can't find item data in JSON")
        del crawler
        return -1

    link = (
        item_url
        if item_url
        else "%s/%s/%s" % (link_prefix, item.get("sid", ""), item.get("id", ""))
    )
    item_id = URL.get_short_md5_name(URL.get_url_path(link))

    # 이미지 다운로드 및 병합
    bg_img_url = item["bgImg"]
    if bg_img_url.endswith(".webp.jpg"):
        bg_img_url = bg_img_url[:-4]  # .webp.jpg -> .webp
    main_img_url = item["mainImg"]
    if main_img_url.endswith(".webp.png"):
        main_img_url = main_img_url[:-4]  # .webp.png -> .webp
    merged_image_url = download_and_merge(
        crawler, download_dir_path, bg_img_url, main_img_url, item_id
    )

    del crawler

    if not merged_image_url:
        LOGGER.warning("can't download and merge images, skipping this feed item")
        return 0

    item["mergedImage"] = merged_image_url

    # HTML 생성 및 출력
    description = compose_description(item, link)

    print(header_str, end="")
    print(description, end="")
    print(
        FeedMaker.get_image_tag_str("https://terzeron.com", "kakaowebtoon.xml", link),
        end="",
    )

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessKakaowebtoon(unittest.TestCase):
            # --- compose_description ---

            def test_compose_description_basic(self):
                item = {
                    "title": "Toon",
                    "genre": "Action",
                    "synopsis": "story",
                    "mergedImage": "http://img.test/x.png",
                }
                out = compose_description(item, "http://l.test/1")
                self.assertIn("<div>Toon</div>", out)
                self.assertIn("<div>Action</div>", out)
                self.assertIn("<div>story</div>", out)
                self.assertIn("<img src='http://img.test/x.png'>", out)

            def test_compose_description_truncates_synopsis(self):
                item = {"title": "T", "synopsis": "x" * 300}
                out = compose_description(item, "l")
                self.assertIn("<div>" + "x" * 200 + "</div>", out)

            def test_compose_description_omits_image_when_absent(self):
                item = {"title": "T"}
                out = compose_description(item, "l")
                self.assertNotIn("<img", out)

            # --- extract_next_data ---

            def test_extract_next_data_basic(self):
                content = (
                    'before<script id="__NEXT_DATA__" type="application/json">'
                    '{"a":1}</script>after'
                )
                self.assertEqual(extract_next_data(content), '{"a":1}')

            def test_extract_next_data_missing(self):
                self.assertIsNone(extract_next_data("<div>no data</div>"))

            # --- select_content_item ---

            def test_select_content_item_by_string_id(self):
                content_map = {"3802": {"title": "A"}, "1": {"title": "B"}}
                self.assertEqual(
                    select_content_item(content_map, "http://x/3802"), {"title": "A"}
                )

            def test_select_content_item_by_int_id(self):
                content_map = {3802: {"title": "A"}}
                self.assertEqual(
                    select_content_item(content_map, "http://x/3802"), {"title": "A"}
                )

            def test_select_content_item_falls_back_to_first(self):
                content_map = {"99": {"title": "first"}, "100": {"title": "second"}}
                self.assertEqual(
                    select_content_item(content_map, ""), {"title": "first"}
                )

            def test_select_content_item_unmatched_id_falls_back(self):
                content_map = {"1": {"title": "only"}}
                self.assertEqual(
                    select_content_item(content_map, "http://x/999"), {"title": "only"}
                )

            # --- end-to-end with sampled upstream pipeline data (network mocked) ---
            # 이 스크립트의 stdin은 webtoon.kakao.com content 페이지(<script id="__NEXT_DATA__">)다.
            # 실 페이지의 contentMap은 클라이언트 XHR로 하이드레이션돼 어떤 crawler fetch에서도 비어있어
            # 직접 샘플링이 불가하므로, 실제 구조(props.initialState.content.contentMap)에 실값을 채운
            # content 페이지를 입력으로 사용한다.
            # main()이 처리하는 핵심 경로(extract_next_data → select_content_item → compose_description)를
            # 그대로 태우고, 네트워크(이미지 다운로드/병합) 결과는 mergedImage mock 값으로 대체한다.
            REAL_SAMPLE_CONTENT = (
                '<script id="__NEXT_DATA__" type="application/json">'
                '{"props":{"initialState":{"content":{"contentMap":{'
                '"342537":{"id":342537,"sid":"레드스톰---왕의-귀환","title":"레드스톰 - 왕의 귀환",'
                '"genre":"액션","synopsis":"검술명가 막내의 복수극","bgImg":"https://kr-a.kakaopagecdn.com/bg.webp",'
                '"mainImg":"https://kr-a.kakaopagecdn.com/main.webp"}'
                "}}}}}</script>"
            )

            def test_real_sample_end_to_end(self):
                item_url = (
                    "https://webtoon.kakao.com/content/레드스톰---왕의-귀환/342537"
                )
                json_content = extract_next_data(self.REAL_SAMPLE_CONTENT)
                self.assertIsNotNone(json_content)
                content_map = json.loads(json_content)["props"]["initialState"][
                    "content"
                ]["contentMap"]
                item = select_content_item(content_map, item_url)
                self.assertEqual(item["title"], "레드스톰 - 왕의 귀환")
                # 이미지 다운로드/병합(네트워크)은 mock 값으로 대체
                item["mergedImage"] = (
                    "https://terzeron.com/img/kakaowebtoon/cf_merged.png"
                )
                description = compose_description(item, item_url)
                self.assertIn("<div>레드스톰 - 왕의 귀환</div>", description)
                self.assertIn("<div>액션</div>", description)
                self.assertIn("<div>검술명가 막내의 복수극</div>", description)
                self.assertIn(f"<a href='{item_url}'>{item_url}</a>", description)
                self.assertIn(
                    "<div><img src='https://terzeron.com/img/kakaowebtoon/cf_merged.png'></div>",
                    description,
                )

        sys.exit(unittest.main())
    else:
        sys.exit(main())
