#!/usr/bin/env python

import sys
import os
import re
import getopt
import logging
import logging.config
from typing import List, Dict, Tuple
from bin.feed_maker_util import IO


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
logger = logging.getLogger(__name__)


HARDCODED_EXCLUDE_PATTERN_STR = r"(?:cang[0-9].jpg|blank.gif)"


def convert_list_to_count_list(l: List[str]) -> List[Tuple[str, int]]:
    count_list: Dict[str, int] = {}
    for item in l:
        if item in count_list:
            count_list[item] += 1
        else:
            count_list[item] = 1
    return sorted(count_list.items(), key=lambda item: item[1], reverse=True)


def get_minors_pattern_from_count_list(l: List[Tuple[str, int]]) -> str:
    pattern_str = "("
    if len(l) > 1:
        i: int = 0
        for key, _ in l:
            # logger.debug("key=%s", key)
            if i > 0:
                # 맨앞의 아이템은 빈번하게 출현했던 것이므로 skip
                # 나머지 아이템은 모두 모아서 제외 패턴으로 합침
                if pattern_str == "(":
                    pattern_str += key
                else:
                    pattern_str += "|" + key
            i += 1
            # logger.debug("pattern_str=%s", pattern_str)
        pattern_str += ")"
    else:
        pattern_str = l[0][0]

    return pattern_str


def collect_domains_and_prefixes(line_list: List[str]) -> Tuple[List[str], List[str]]:
    """각 줄의 img URL에서 domain과 prefix를 추출해 등장 순서대로 두 리스트로 반환."""
    domain_list: List[str] = []
    prefix_list: List[str] = []
    for line in line_list:
        m = re.search(
            r"<img src=\'(?P<img_url>https?://[^\'>]+)\'(\S+width=.*)?/?>", line
        )
        if m:
            img_url = m.group("img_url")
            m = re.search(
                r"(?P<domain>https?://[^/]+)(?P<prefix>/[^\.]+)/[^/]+\.(?:jpg|png|gif)",
                img_url,
            )
            if m:
                domain_list.append(m.group("domain"))
                prefix_list.append(m.group("prefix"))
    return domain_list, prefix_list


def filter_image_lines(
    line_list: List[str], domain_excl_pattern_str: str, prefix_excl_pattern_str: str
) -> List[str]:
    """소수 domain/prefix 패턴과 하드코딩 제외 패턴에 걸리는 줄을 빼고 남길 줄 목록을 반환."""
    new_pattern = (
        r""
        + domain_excl_pattern_str
        + prefix_excl_pattern_str
        + r"/[^/]+\.(?:jpg|png|gif)"
    )
    result: List[str] = []
    for line in line_list:
        if (
            domain_excl_pattern_str
            and prefix_excl_pattern_str
            and re.search(new_pattern, line)
        ):
            continue
        if re.search(HARDCODED_EXCLUDE_PATTERN_STR, line):
            continue
        result.append(line)
    return result


def main():
    _, args = getopt.getopt(sys.argv[1:], "n:f:")

    line_list = IO.read_stdin_as_line_list()
    domain_list, prefix_list = collect_domains_and_prefixes(line_list)

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
    for line in filter_image_lines(
        line_list, domain_excl_pattern_str, prefix_excl_pattern_str
    ):
        print(line, end="")


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestRemoveAnchorImages(unittest.TestCase):
            # --- convert_list_to_count_list ---

            def test_convert_list_to_count_list_counts(self):
                self.assertEqual(
                    convert_list_to_count_list(["a", "a", "b"]), [("a", 2), ("b", 1)]
                )

            def test_convert_list_to_count_list_sorted_desc(self):
                result = convert_list_to_count_list(["x", "y", "y", "y", "x"])
                self.assertEqual(result[0], ("y", 3))

            def test_convert_list_to_count_list_empty(self):
                self.assertEqual(convert_list_to_count_list([]), [])

            # --- get_minors_pattern_from_count_list ---

            def test_get_minors_pattern_single(self):
                self.assertEqual(
                    get_minors_pattern_from_count_list([("http://a", 5)]), "http://a"
                )

            def test_get_minors_pattern_skips_most_frequent(self):
                # 맨 앞(최빈) 항목은 빠지고 나머지가 |로 묶인다
                self.assertEqual(
                    get_minors_pattern_from_count_list(
                        [("main", 10), ("m1", 2), ("m2", 1)]
                    ),
                    "(m1|m2)",
                )

            # --- collect_domains_and_prefixes ---

            def test_collect_domains_and_prefixes_basic(self):
                lines = ["<img src='https://a.test/sub/img1.jpg'/>"]
                domains, prefixes = collect_domains_and_prefixes(lines)
                self.assertEqual(domains, ["https://a.test"])
                self.assertEqual(prefixes, ["/sub"])

            def test_collect_domains_and_prefixes_no_img(self):
                self.assertEqual(
                    collect_domains_and_prefixes(["<p>text</p>"]), ([], [])
                )

            # --- filter_image_lines ---

            def test_filter_image_lines_removes_minor_pattern(self):
                lines = [
                    "https://minor.test/sub/x.jpg\n",
                    "https://main.test/sub/y.jpg\n",
                ]
                result = filter_image_lines(lines, "(https://minor.test)", "(/sub)")
                self.assertEqual(result, ["https://main.test/sub/y.jpg\n"])

            def test_filter_image_lines_removes_hardcoded(self):
                lines = ["cang1.jpg\n", "blank.gif\n", "keep.jpg\n"]
                result = filter_image_lines(lines, "", "")
                self.assertEqual(result, ["keep.jpg\n"])

            def test_filter_image_lines_no_exclusion_keeps_all(self):
                lines = ["a.png\n", "b.png\n"]
                self.assertEqual(filter_image_lines(lines, "", ""), lines)

        sys.exit(unittest.main())
    else:
        sys.exit(main())
