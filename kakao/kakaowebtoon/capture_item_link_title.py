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
from datetime import datetime
from bin.feed_maker_util import IO, URL, header_str
from bin.feed_maker import FeedMaker
from bin.crawler import Crawler


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def compose_description(item, link) -> str:
    description = "<div>\n"
    description += "    <div>%s</div>\n" % item["title"]
    description += "    <div>%s</div>\n" % ", ".join(item["seoKeywords"])
    description += "    <div>%s</div>\n" % item["catchphraseTwoLines"]
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
    
    return os.environ["WEB_SERVICE_URL"] + "/xml/img/kakaowebtoon/" + merged_image_path.name
    

def main() -> int:
    link_prefix = "https://webtoon.kakao.com/content"
    link = ""
    title = ""
    num_of_recent_feeds = 1000
    feed_dir_path = Path.cwd()

    optlist, _ = getopt.getopt(sys.argv[1:], "n:f:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)
        elif o == "-f":
            feed_dir_path = Path(a)

    crawler = Crawler()
    download_dir_path = Path(os.environ["WEB_SERVICE_FEEDS_DIR"]) / "img" / "kakaowebtoon"
        
    content = IO.read_stdin()
    content = re.sub(r'(^(<\S[^>]*>)+|(<\S[^>]*>)+$)', '', content)
    result_list = []
    json_data = json.loads(content)
    if "data" not in json_data:
        return -1
    if "sections" not in json_data["data"]:
        return -1

    for section in json_data["data"]["sections"]:
        # section == weekday
        if "cardGroups" not in section:
            continue
        for card_group in section["cardGroups"]:
            if "cards" not in card_group:
                continue
            for card in card_group["cards"]:
                if "content" not in card:
                    continue

                item = card["content"]
                if "adult" in item and item["adult"]:
                    continue

                date_str = "1970-01-01"
                if "serialRestartDateTime" in item and item["serialRestartDateTime"]:
                    date_str = str(datetime.fromisoformat(item["serialRestartDateTime"]).date())
                elif "serialStartDateTime" in item and item["serialStartDateTime"]:
                    date_str = str(datetime.fromisoformat(item["serialStartDateTime"]).date())
                    
                link = "%s/%s/%s" % (link_prefix, item["seoId"], item["id"])
                item_id = URL.get_short_md5_name(URL.get_url_path(link))
                title = date_str + " " + item["title"]
                result_list.append((link, title))

                # 특수한 처리 - extraction 단계를 여기서 수행
                merged_image_url = download_and_merge(crawler, download_dir_path, item["backgroundImage"] + ".webp", item["featuredCharacterImageA"] + ".png", item_id)
                if not merged_image_url:
                    continue
                item["mergedImage"] = merged_image_url
                description = compose_description(item, link)
                html_file_name = item_id + ".html"
                file_path = feed_dir_path / "html" / html_file_name

                if os.path.isfile(file_path):
                    continue
                with open(file_path, 'w', encoding="utf-8") as fp:
                    fp.write(header_str)
                    fp.write(description)
                    fp.write(FeedMaker.get_image_tag_str("https://terzeron.com", "kakaowebtoon.xml", link))

                    
    del crawler
    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

    return 0


if __name__ == "__main__":
    sys.exit(main())
