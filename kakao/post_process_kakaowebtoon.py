#!/usr/bin/env python

import os
import sys
import re
import json
import pprint
import getopt
import requests
import urllib.parse
import logging
import logging.config
from feedmakerutil import IO, Config


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
logger = logging.getLogger()


def get_page_content(url, encoding, data, header):
    #print(data, header)
    response = requests.post(url, data = data, headers = header)
    return response.text


def main():
    for line in sys.stdin:
        pass
    
    img_url_prefix = "https://page-edge.kakao.com/sdownload/resource?kid="

    page_url = sys.argv[1]
    parsed_url = urllib.parse.urlparse(page_url)
    qs = urllib.parse.parse_qs(parsed_url.query)
    product_id = qs["productId"][0]

    config = Config()
    extraction_conf = config.get_extraction_configs()
    encoding = extraction_conf["encoding"]
    user_agent_str = extraction_conf["user_agent"]
    
    api_url = "https://api2-page.kakao.com/api/v1/inven/get_download_data/web"
    header = {"User-Agent": user_agent_str}
    data = {"productId": product_id, "deviceId": "07fb8773b324c189df8d99dc6c296838"}
    page_content = get_page_content(api_url, encoding, data, header)
    data = json.loads(page_content)
    #pprint.pprint(data)

    payload_data = {"kid": "69Vgy9MJUN_wIMJUuweDplg8m3g_-1LRzEb1XdkLHkxOJzkZvsbxV1-9X7c0r0ne", "filename": "2714917_1524018558739.jpeg", "signature": "yqY1bdCdGHyTNt5ekOTrQTEzKkM%3D&", "expires": "1524492621", "credential": "lUt9i42FY2I4ggejDuJPPXMt5QR0LkfX"}

    if "downloadData" in data:
        if "members" in data["downloadData"]:
            if "files" in data["downloadData"]["members"]:
                for file in data["downloadData"]["members"]["files"]:
                    #pprint.pprint(file)
                    img_url = img_url_prefix + file["secureUrl"]
                    print("<img src='%s'>" % img_url)


if __name__ == "__main__":
    sys.exit(main())
