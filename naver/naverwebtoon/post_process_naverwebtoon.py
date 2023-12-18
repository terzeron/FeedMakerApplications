#!/usr/bin/env python


import sys
import os
import re
import json
import getopt
import logging
import logging.config
from typing import List
from pathlib import Path
from bin.feed_maker_util import IO, Config, URL, header_str
from bin.crawler import Crawler


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def print_img_tag(feed_dir_path: Path, page_url: str) -> None:
    config = Config(feed_dir_path)
    if not config:
        LOGGER.error("can't read configuration")
        return
    rss_conf = config.get_rss_configs()
    m = re.search(r'https://[^/]+/(?P<rss_file_name>.+\.xml)', rss_conf["rss_link"])
    if m:
        rss_file_name = m.group("rss_file_name")
        md5_name = URL.get_short_md5_name(URL.get_url_path(page_url))
        print("<img src='https://terzeron.com/img/1x1.jpg?feed=%s&item=%s'/>" % (rss_file_name, md5_name))


def main() -> int:
    feed_dir_path = Path.cwd()
    url_prefix = "https://comic.naver.com/api/article/list/info?titleId="
    exclude_keywords = ["로맨스", "연인", "연애", "키스", "짝사랑", "고백", "유부녀", "황후", "왕후", "왕비", "공녀", "첫사랑", "재벌", "순정", "후궁", "로판", "로맨스판타지", "멜로", "혐관로맨스", "힐링", "연상연하", "아이돌", "감성", "감성드라마", "무해한", "일상", "사이다", "러블리", "햇살캐", "계략여주", "괴담", "까칠남", "캠퍼스로맨스", "구원서사", "소꿉친구", "청춘로맨스", "친구>연인", "하이틴", "학원로맨스", "현실로맨스", "다정남", "집착물", "연예계", "인플루언서", "걸크러시", "하이틴", "성별반전", "육아물", "삼각관계", "사이비종교", "궁중로맨스"]

    IO.read_stdin()

    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        if o == "-n":
            _ = int(a)

    tag_list: List = []
    page_url = args[0]
    m = re.search(r'titleId=(?P<title_id>\d+)', page_url)
    if m:
        title_id = m.group("title_id")
        link = url_prefix + title_id
        crawler = Crawler(dir_path=feed_dir_path)
        result, error, _ = crawler.run(link)
        if error:
            LOGGER.error(f"Error: can't get data from '{link}'")
            return -1

        json_data = json.loads(result)
        
        if "curationTagList" in json_data:
            for curation in json_data["curationTagList"]:
                if "tagName" in curation:
                    if curation["tagName"] in exclude_keywords:
                        return 0
                    tag_list.append(curation["tagName"])
                    
        if "titleName" in json_data:
            title_name = json_data["titleName"]
        if "synopsis" in json_data:
            synopsis = json_data["synopsis"]
        if "thumbnailUrl" in json_data:
            thumbnail_url = json_data["thumbnailUrl"]
            
        print(header_str)
        print("<p>" + title_name + "</p>")
        print("<p>" + synopsis + "</p>")
        print("<p><img src='" + thumbnail_url + "'></p>")
        print("<ul>")
        for tag in tag_list:
            print("<li>#" + tag + "</li>")
        print("</ul>")
        print_img_tag(feed_dir_path, page_url)

    return 0


if __name__ == "__main__":
    sys.exit(main())
