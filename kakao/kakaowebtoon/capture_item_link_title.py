#!/usr/bin/env python3


import sys
import json
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    num = ""
    state = 0
    url_prefix = "http://page.kakao.com/home/"

    json_content = IO.read_stdin()
    data = json.loads(json_content)
    if "section_containers" in data:
        for container in data["section_containers"]:
            if "section_series" in container:
                for section in container["section_series"]:
                    if "list" in section:
                        for item in section["list"]:
                            link = url_prefix + str(item["series_id"])
                            title = item["title"]
                            print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
