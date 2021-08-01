#!/usr/bin/env python

import os
import sys
import json
#import pprint
import urllib.parse
import logging
import logging.config
import requests
from feed_maker_util import Config


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/bin/logging.conf")
logger = logging.getLogger()


def get_page_content(url, data, header):
    #print(data, header)
    response = requests.post(url, data=data, headers=header)
    return response.text


def main():
    for line in sys.stdin:
        pass

    img_url_prefix = "https://page-edge-jz.kakao.com/sdownload/resource/"

    page_url = sys.argv[1]
    parsed_url = urllib.parse.urlparse(page_url)
    qs = urllib.parse.parse_qs(parsed_url.query)
    product_id = qs["productId"][0]

    config = Config()
    extraction_conf = config.get_extraction_configs()
    #encoding = extraction_conf["encoding"]
    user_agent_str = extraction_conf["user_agent"]

    api_url = "https://api2-page.kakao.com/api/v1/inven/get_download_data/web"
    header = {"User-Agent": user_agent_str}
    data = {"productId": product_id, "deviceId": "07fb8773b324c189df8d99dc6c296838"}
    page_content = get_page_content(api_url, data, header)
    data = json.loads(page_content)
    #pprint.pprint(data)

    if "downloadData" in data:
        if "members" in data["downloadData"]:
            if "files" in data["downloadData"]["members"]:
                for file in data["downloadData"]["members"]["files"]:
                    #pprint.pprint(file)
                    img_url = img_url_prefix + file["secureUrl"]
                    print("<img src='%s'>" % img_url)


if __name__ == "__main__":
    sys.exit(main())
