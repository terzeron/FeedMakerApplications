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
    description += "    <div><img src='%s'></div>\n" % (item["mergedImage"])
    description += "</div>\n"
    return description


def download_and_merge(crawler: Crawler, download_dir_path: Path, background_image_url: str, foreground_image_url: str, item_id: str) -> str:
    background_image_path = download_dir_path / (item_id + "_background.webp")
    foreground_image_path = download_dir_path / (item_id + "_foreground.png")
    merged_image_path = download_dir_path / (item_id + ".png")

    if not background_image_path.is_file() or background_image_path.stat().st_size == 0:
        result, error, _ = crawler.run(background_image_url, download_file=background_image_path)
        if not result or error:
            LOGGER.error("can't download background image '%s' to '%s', %s", background_image_url, background_image_path, error)
            return ""

    if not foreground_image_path.is_file() or foreground_image_path.stat().st_size == 0:
        result, error, _ = crawler.run(foreground_image_url, download_file=foreground_image_path)
        if not result or error:
            LOGGER.error("can't download foreground image '%s' to '%s', %s", foreground_image_url, foreground_image_path, error)
            return ""

    if not merged_image_path.is_file() or merged_image_path.stat().st_size == 0:
        cropped_background_image_path = download_dir_path / (item_id + "_cropped_background.webp")
        result = subprocess.run(["convert", str(background_image_path), "-crop", "750x824+0+0", "+repage", str(cropped_background_image_path)], capture_output=True, text=True, check=True)
        if result.returncode != 0:
            LOGGER.error("can't merge images '%s' and '%s' to '%s'", background_image_path, cropped_background_image_path, merged_image_path)
            return ""
        result = subprocess.run(["convert", str(cropped_background_image_path), str(foreground_image_path), "-gravity", "south", "-composite", str(merged_image_path)], capture_output=True, text=True, check=True)
        if result.returncode != 0:
            LOGGER.error("can't merge images '%s' and '%s' to '%s'", cropped_background_image_path, foreground_image_path, merged_image_path)
            return ""

    return Env.get("WEB_SERVICE_IMAGE_URL_PREFIX") + "/kakaowebtoon/" + merged_image_path.name


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
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', content)
    if not match:
        LOGGER.error("can't find __NEXT_DATA__ in HTML")
        del crawler
        return -1

    json_content = match.group(1)

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
        # contentMap에서 첫 번째 항목 또는 URL에서 추출한 ID로 찾기
        content_id = None
        if item_url:
            # URL에서 ID 추출 (예: .../3802)
            id_match = re.search(r'/(\d+)$', item_url)
            if id_match:
                content_id = id_match.group(1)

        if content_id and content_id in content_map:
            item = content_map[content_id]
        elif content_id and int(content_id) in content_map:
            item = content_map[int(content_id)]
        else:
            # 첫 번째 항목 사용
            item = next(iter(content_map.values()))
    except (KeyError, TypeError) as e:
        LOGGER.error("can't find content in JSON structure: %s", e)
        del crawler
        return -1

    if not item or "title" not in item:
        LOGGER.error("can't find item data in JSON")
        del crawler
        return -1

    link = item_url if item_url else "%s/%s/%s" % (link_prefix, item.get("sid", ""), item.get("id", ""))
    item_id = URL.get_short_md5_name(URL.get_url_path(link))

    # 이미지 다운로드 및 병합
    merged_image_url = download_and_merge(
        crawler,
        download_dir_path,
        item["bgImg"],
        item["mainImg"],
        item_id
    )

    del crawler

    if not merged_image_url:
        LOGGER.error("can't download and merge images")
        return -1

    item["mergedImage"] = merged_image_url

    # HTML 생성 및 출력
    description = compose_description(item, link)

    print(header_str, end="")
    print(description, end="")
    print(FeedMaker.get_image_tag_str("https://terzeron.com", "kakaowebtoon.xml", link), end="")

    return 0


if __name__ == "__main__":
    sys.exit(main())
