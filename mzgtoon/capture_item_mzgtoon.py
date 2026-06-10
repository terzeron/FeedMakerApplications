#!/usr/bin/env python


import os
import sys
import getopt
import json
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


def extract_items(data: dict, url_prefix: str) -> List[Tuple[str, str]]:
    """listData에서 list_id/list_episode로 링크를 만들고 (link, title) 목록을 만든다."""
    result_list: List[Tuple[str, str]] = []
    for item in data.get("listData", []):
        item_id = item.get("list_id", 0)
        episode = item.get("list_episode", 0)
        title = item.get("list_title", "")
        link = f"{url_prefix}/{item_id}/{episode}"
        result_list.append((link, title))
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

    url_prefix = get_url_prefix_from_config(feed_dir_path)

    content = IO.read_stdin()
    data = json.loads(content)
    result_list = extract_items(data, url_prefix)

    for line in render_lines(result_list, num_of_recent_feeds):
        print(line)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest
        from unittest.mock import MagicMock, patch

        class TestCaptureItemMzgtoon(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default_num(self):
                self.assertEqual(parse_args([])[1], 1000)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"])[1], 5)

            def test_parse_args_feed_dir(self):
                self.assertEqual(parse_args(["-f", "/tmp/x"])[0], Path("/tmp/x"))

            # --- get_url_prefix_from_config ---

            def test_get_url_prefix_from_config_builds_webtoon_url(self):
                mock_config = MagicMock()
                mock_config.get_collection_configs.return_value = {
                    "list_url_list": ["https://mzg.test/list"]
                }
                with (
                    patch("__main__.Config", return_value=mock_config),
                    patch("__main__.URL.get_url_scheme", return_value="https"),
                    patch("__main__.URL.get_url_domain", return_value="mzg.test"),
                ):
                    self.assertEqual(
                        get_url_prefix_from_config(Path(".")),
                        "https://mzg.test/webtoon",
                    )

            def test_get_url_prefix_from_config_raises_without_url(self):
                mock_config = MagicMock()
                mock_config.get_collection_configs.return_value = {"list_url_list": []}
                with patch("__main__.Config", return_value=mock_config):
                    with self.assertRaises(InsufficientConfigError):
                        get_url_prefix_from_config(Path("."))

            # --- extract_items ---

            def test_extract_items_basic(self):
                data = {
                    "listData": [
                        {"list_id": 10, "list_episode": 3, "list_title": "ep3"}
                    ]
                }
                self.assertEqual(
                    extract_items(data, "https://m.test/webtoon"),
                    [("https://m.test/webtoon/10/3", "ep3")],
                )

            def test_extract_items_multiple(self):
                data = {
                    "listData": [
                        {"list_id": 1, "list_episode": 1, "list_title": "A"},
                        {"list_id": 1, "list_episode": 2, "list_title": "B"},
                    ]
                }
                self.assertEqual([t for _, t in extract_items(data, "p")], ["A", "B"])

            def test_extract_items_defaults_for_missing_fields(self):
                self.assertEqual(
                    extract_items({"listData": [{}]}, "p"), [("p/0/0", "")]
                )

            def test_extract_items_no_list_data(self):
                self.assertEqual(extract_items({}, "p"), [])

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

        sys.exit(unittest.main())
    else:
        sys.exit(main())
