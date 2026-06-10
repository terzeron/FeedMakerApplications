#!/usr/bin/env python


import os
import sys
import re
import getopt
from pathlib import Path
from typing import List, Tuple
from bin.feed_maker_util import IO, URL, Config


def get_url_from_config(feed_dir_path: Path):
    config = Config(feed_dir_path=feed_dir_path)
    collection = config.get_collection_configs()
    url = collection["list_url_list"][0]
    return url


def parse_args(argv: List[str]) -> Tuple[Path, int]:
    """명령행 인자를 파싱해 (feed_dir_path, num_of_recent_feeds)를 반환."""
    feed_dir_path = Path.cwd()
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        elif o == "-n":
            num_of_recent_feeds = int(a)
    return feed_dir_path, num_of_recent_feeds


def parse_feed_list(line_list: List[str], site_url: str) -> List[Tuple[str, str]]:
    """</p>로 쪼갠 각 조각에서 anchor href와 제목을 뽑아 (link, title) 목록을 만든다."""
    result_list: List[Tuple[str, str]] = []
    for chunk in line_list:
        for line in chunk.split("</p>"):
            m = re.search(
                r'<a href="(?P<link>[^"]+)"[^>]*>\s*<div [^>]*>\s*<p [^>]*>(?P<title>[^<]+)',
                line,
            )
            if m:
                link = URL.concatenate_url(site_url, m.group("link"))
                title = m.group("title")
                result_list.append((link, title))
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """(link, title) 목록을 'link\\ttitle' 라인 목록으로 변환."""
    return [
        "%s\t%s" % (link, title) for (link, title) in result_list[:num_of_recent_feeds]
    ]


def main() -> int:
    feed_dir_path, num_of_recent_feeds = parse_args(sys.argv[1:])

    if not feed_dir_path or not feed_dir_path.is_dir():
        LOGGER.error(f"can't find such a directory '{feed_dir_path}'")
        return -1

    site_url = get_url_from_config(feed_dir_path)

    line_list = IO.read_stdin_as_line_list()
    result_list = parse_feed_list(line_list, site_url)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)

    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest
        from unittest.mock import patch

        class TestCaptureItemBlacktoon(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default_num(self):
                self.assertEqual(parse_args([])[1], 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"])[1], 5)

            def test_parse_args_feed_dir(self):
                self.assertEqual(parse_args(["-f", "/tmp/x"])[0], Path("/tmp/x"))

            # --- parse_feed_list ---

            def _chunk(self, link, title):
                return f'<a href="{link}" class="c"> <div class="d"> <p class="t">{title}</p></a>'

            def test_parse_feed_list_basic(self):
                with patch(
                    "__main__.URL.concatenate_url",
                    side_effect=lambda base, rel: base + rel,
                ):
                    result = parse_feed_list(
                        [self._chunk("/ep/1", "Title One")], "https://b.test"
                    )
                self.assertEqual(result, [("https://b.test/ep/1", "Title One")])

            def test_parse_feed_list_multiple_in_one_chunk(self):
                chunk = self._chunk("/ep/1", "A") + "</p>" + self._chunk("/ep/2", "B")
                with patch(
                    "__main__.URL.concatenate_url",
                    side_effect=lambda base, rel: base + rel,
                ):
                    result = parse_feed_list([chunk], "https://b.test")
                self.assertEqual([t for _, t in result], ["A", "B"])

            def test_parse_feed_list_no_match(self):
                with patch(
                    "__main__.URL.concatenate_url", side_effect=lambda b, r: b + r
                ):
                    self.assertEqual(
                        parse_feed_list(["<div>noise</div>"], "https://b.test"), []
                    )

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([], "https://b.test"), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 1000),
                    ["l1\tA", "l2\tB"],
                )

            def test_render_lines_limit(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B"), ("l3", "C")], 2),
                    ["l1\tA", "l2\tB"],
                )

            def test_render_lines_empty(self):
                self.assertEqual(render_lines([], 1000), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
