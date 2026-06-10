#!/usr/bin/env python


import os
import sys
import getopt
import re
from pathlib import Path
from typing import List, Tuple
from bin.feed_maker_util import IO, Config, URL


class InsufficientConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)


def get_url_prefix_from_config(feed_dir_path: Path):
    config = Config(feed_dir_path)
    conf = config.get_collection_configs()
    url_list = conf.get("list_url_list", [])
    if url_list:
        url = url_list[0]
        return URL.get_url_scheme(url) + "://" + URL.get_url_domain(url) + "/webtoon"
    raise InsufficientConfigError("Can't get url prefix from configuration")


def parse_args(argv: List[str]) -> Tuple[Path, int]:
    """명령행 인자를 파싱해 (feed_dir_path, num_of_recent_feeds)를 반환."""
    feed_dir_path = Path.cwd()
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(argv, "n:f:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
        elif o == "-f":
            feed_dir_path = Path(a)
    return feed_dir_path, num_of_recent_feeds


def parse_feed_list(line_list: List[str]) -> List[Tuple[str, str]]:
    """flex 컨테이너 → anchor 링크 → class 줄 → 제목 순으로 상태머신을 돌려 (link, title) 목록을 만든다."""
    link = ""
    state = 0
    result_list: List[Tuple[str, str]] = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<div class="flex items-center">', line)
            if m:
                state = 1
        elif state == 1:
            m = re.search(r'<a href="(?P<link>[^"]+)"', line)
            if m:
                link = m.group("link")
                state = 2
        elif state == 2:
            m = re.search(r'class="[^"]+"', line)
            if m:
                state = 3
        elif state == 3:
            m = re.search(r"^\s*(?P<title>\S.+\S)\s*$", line)
            if m:
                title = m.group("title")
                result_list.append((link, title))
                state = 1
    return result_list


def render_lines(
    result_list: List[Tuple[str, str]], num_of_recent_feeds: int
) -> List[str]:
    """(link, title) 목록을 'link\\ttitle' 라인 목록으로 변환."""
    return [
        "%s\t%s" % (link, title) for (link, title) in result_list[:num_of_recent_feeds]
    ]


def main():
    feed_dir_path, num_of_recent_feeds = parse_args(sys.argv[1:])

    line_list = IO.read_stdin_as_line_list()
    result_list = parse_feed_list(line_list)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest
        from unittest.mock import MagicMock, patch

        class TestCaptureItemJoatoon(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default_num(self):
                self.assertEqual(parse_args([])[1], 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "6"])[1], 6)

            def test_parse_args_feed_dir(self):
                self.assertEqual(parse_args(["-f", "/tmp/x"])[0], Path("/tmp/x"))

            # --- get_url_prefix_from_config ---

            def test_get_url_prefix_from_config_builds_webtoon_url(self):
                mock_config = MagicMock()
                mock_config.get_collection_configs.return_value = {
                    "list_url_list": ["https://joatoon.test/list"]
                }
                with (
                    patch("__main__.Config", return_value=mock_config),
                    patch("__main__.URL.get_url_scheme", return_value="https"),
                    patch("__main__.URL.get_url_domain", return_value="joatoon.test"),
                ):
                    self.assertEqual(
                        get_url_prefix_from_config(Path(".")),
                        "https://joatoon.test/webtoon",
                    )

            def test_get_url_prefix_from_config_raises_without_url(self):
                mock_config = MagicMock()
                mock_config.get_collection_configs.return_value = {"list_url_list": []}
                with patch("__main__.Config", return_value=mock_config):
                    with self.assertRaises(InsufficientConfigError):
                        get_url_prefix_from_config(Path("."))

            # --- parse_feed_list ---

            def _page(self, items):
                lines = []
                for link, title in items:
                    lines.append('<div class="flex items-center">')
                    lines.append(f'<a href="{link}">')
                    lines.append('<span class="title-class">')
                    lines.append(f"{title}")
                return lines

            def test_parse_feed_list_basic(self):
                lines = self._page([("/webtoon/1", "Title One")])
                self.assertEqual(parse_feed_list(lines), [("/webtoon/1", "Title One")])

            def test_parse_feed_list_multiple(self):
                # 제목 정규식이 \S.+\S(최소 3자)를 요구하므로 3자 이상 제목을 쓴다
                lines = self._page([("/w/1", "AAA"), ("/w/2", "BBB")])
                self.assertEqual([t for _, t in parse_feed_list(lines)], ["AAA", "BBB"])

            def test_parse_feed_list_requires_flex_container(self):
                lines = [
                    '<a href="/w/1">',
                    '<span class="c">',
                    "Title",
                ]
                self.assertEqual(parse_feed_list(lines), [])

            def test_parse_feed_list_empty(self):
                self.assertEqual(parse_feed_list([]), [])

            # --- render_lines ---

            def test_render_lines_basic(self):
                self.assertEqual(
                    render_lines([("l1", "A"), ("l2", "B")], 1000), ["l1\tA", "l2\tB"]
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
