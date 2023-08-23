#!/usr/bin/env python

import sys
import os
import re
import getopt
import logging
import logging.config
from typing import List, Dict, Tuple
from bin.feed_maker_util import IO, URL


logging.config.fileConfig(os.environ["FEED_MAKER_HOME_DIR"] + "/logging.conf")
logger = logging.getLogger(__name__)


def convert_list_to_count_list(l: List[str]) -> List[Tuple[str, int]]:
    count_list: Dict[str, int] = {}
    for item in l:
        if item in count_list:
            count_list[item] += 1
        else:
            count_list[item] = 1
    return sorted(count_list.items(), key=lambda item: item[1], reverse=True)


def get_minors_pattern_from_count_list(l: List[Tuple[str, int]]) -> str:
    pattern_str = '('
    if len(l) > 1:
        i: int = 0
        for key, _ in l:
            #logger.debug("key=%s", key)
            if i > 0:
                # 맨앞의 아이템은 빈번하게 출현했던 것이므로 skip
                # 나머지 아이템은 모두 모아서 제외 패턴으로 합침
                if pattern_str == '(':
                    pattern_str += key
                else:
                    pattern_str += "|" + key
            i += 1
            #logger.debug("pattern_str=%s", pattern_str)
        pattern_str += ')'
    else:
        pattern_str = l[0][0]

    return pattern_str


def main():
    _, args = getopt.getopt(sys.argv[1:], "n:f:")

    line_list = IO.read_stdin_as_line_list()
    domain_list: List[str] = []
    prefix_list: List[str] = []
    for line in line_list:
        m = re.search(r'<img src=\'(?P<img_url>https?://[^\'>]+)\'(\S+width=.*)?/?>', line)
        if m:
            img_url = m.group("img_url")
            #logger.debug("img_url=%s", img_url)
            m = re.search(r'(?P<domain>https?://[^/]+)(?P<prefix>/[^\.]+)/[^/]+\.(?:jpg|png|gif)', img_url)
            if m:
                domain_list.append(m.group("domain"))
                prefix_list.append(m.group("prefix"))
    #logger.debug("domain_list=%r", domain_list)
    #logger.debug("prefix_list=%r", prefix_list)

    # 예외적인 url domain 식별
    domain_count_list = convert_list_to_count_list(domain_list)
    logger.debug("domain_count_list=%r", domain_count_list)
    domain_excl_pattern_str = get_minors_pattern_from_count_list(domain_count_list)
    logger.debug("domain_excl_pattern_str=%s", domain_excl_pattern_str)

    # 예외적인 url prefix 식별
    prefix_count_list = convert_list_to_count_list(prefix_list)
    logger.debug("prefix_count_list=%r", prefix_count_list)
    # 제외 패턴 조합
    prefix_excl_pattern_str = get_minors_pattern_from_count_list(prefix_count_list)
    logger.debug("prefix_excl_pattern_str=%s", prefix_excl_pattern_str)

    # 출력
    hardcoded_exclude_pattern_str = r'(?:cang[0-9].jpg|blank.gif)'
    new_pattern = r'' + domain_excl_pattern_str + prefix_excl_pattern_str + r'/[^/]+\.(?:jpg|png|gif)'
    logger.debug("new_pattern=%s", new_pattern)
    for line in line_list:
        if domain_excl_pattern_str and prefix_excl_pattern_str and re.search(new_pattern, line):
            continue
        if re.search(hardcoded_exclude_pattern_str, line):
            continue
        print(line, end='')


if __name__ == "__main__":
    sys.exit(main())
