#!/usr/bin/env python

#cat - | egrep -v "(cang[0-9].jpg|blank.gif)"
import sys
import re
from typing import List, Dict
from feed_maker_util import IO


def main():
    line_list = IO.read_stdin_as_line_list()
    img_url_prefix_list: List[str] = []
    for line in line_list:
        m = re.search(r'<img src=\'(?P<img_url>http[^\'>]+)\'(\s+width=.*)?/>', line)
        if m:
            img_url = m.group("img_url")
            m = re.search(r'comic/(?P<prefix>\w+)\/', img_url)
            if m:
                img_url_prefix_list.append(m.group("prefix"))
    #print("img_url_prefix_list=", img_url_prefix_list)
      
    # 예외적인 url prefix 식별
    prefix_count_map: Dict[str, int] = {}
    for prefix in img_url_prefix_list:
        if prefix in prefix_count_map:
            prefix_count_map[prefix] += 1
        else:
            prefix_count_map[prefix] = 1
    prefix_count_map = sorted(prefix_count_map.items(), key=lambda x: x[1], reverse=True)
    #print("prefix_count_map=", prefix_count_map)

    # 제외 패턴 조합
    exclude_pattern_prefix = r'comic/(?:'
    exclude_pattern_str: str = exclude_pattern_prefix
    if len(prefix_count_map) > 1:
        i: int = 0
        for prefix, _ in prefix_count_map:
            if i > 0:
                if exclude_pattern_str == exclude_pattern_prefix:
                    exclude_pattern_str += prefix
                else:
                    exclude_pattern_str += "|" + prefix

            #print(prefix, count)
            i += 1
        exclude_pattern_str += ")"
    else:
        exclude_pattern_str = None
    #print("exclude_pattern_str=", exclude_pattern_str)

    # 출력
    hardcoded_exclude_pattern_str = r'(?:cang[0-9].jpg|blank.gif)'
    for line in line_list:
        if exclude_pattern_str and re.search(exclude_pattern_str, line):
            continue
        if re.search(hardcoded_exclude_pattern_str, line):
            continue
        print(line, end='')


if __name__ == "__main__":
    sys.exit(main())
