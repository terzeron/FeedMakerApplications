#!/usr/bin/env python


import sys
import json
from feed_maker_util import IO


def main():
    link = ""
    title = ""
    url_prefix = "http://page.kakao.com/home?seriesId="

    json_content = IO.read_stdin()
    data = json.loads(json_content)
    if "section_containers" in data:
        for container in data["section_containers"]:
            if "section_series" in container:
                for section in container["section_series"]:
                    if "list" in section:
                        data_list = section["list"]
                        for item in data_list:
                            if item["age_grade"] == 0:
                                link = url_prefix + str(item["series_id"])
                                title = item["title"] 
                                if item["waitfree"] == "Y":
                                    continue
                                print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
