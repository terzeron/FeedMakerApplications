#!/usr/bin/env python


import os
import sys
import re
import subprocess
import logging
import logging.config
from typing import Tuple
from bin.feed_maker_util import IO


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
logger = logging.getLogger()


def parse_input(line_list) -> Tuple[str, str]:
    """입력에서 이미지 url prefix와 documentURL(data_url)을 추출한다."""
    url_prefix = ""
    data_url = ""
    for line in line_list:
        m = re.search(r"jpg: '(?P<url_prefix>[^']+\/){=filename}\?type=[^']+'", line)
        if m:
            url_prefix = m.group("url_prefix")
        else:
            m = re.search(r"documentURL:\s*'(?P<data_url>[^']+)'", line)
            if m:
                data_url = m.group("data_url")
                break
    return url_prefix, data_url


def main():
    page_url = sys.argv[1]

    url_prefix, data_url = parse_input(IO.read_stdin_as_line_list())

    if not data_url or url_prefix:
        logger.error("can't get a data url from input")
        return -1

    cmd = "wget.sh '%s' utf8 | gunzip 2> /dev/null || wget.sh '%s' utf8" % (
        data_url,
        data_url,
    )
    with subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE) as p:
        for line in p.stdout:
            line = line.rstrip()
            matches = re.findall(
                r"[^\"]+\"\s*:\s*\"(assets/still/[^\"]+\.(?:png|jpg))\"", line
            )
            for match in matches:
                img_url = url_prefix + match[0]
                print("<img src='%s' width='100%'/>" % (img_url))


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestPostProcessNaverwebtoonOzviewer(unittest.TestCase):
            def test_parse_input_data_url(self):
                lines = ["noise", "documentURL: 'http://oz.test/data.json'", "after"]
                self.assertEqual(parse_input(lines), ("", "http://oz.test/data.json"))

            def test_parse_input_stops_at_first_document_url(self):
                lines = [
                    "documentURL: 'http://oz.test/first'",
                    "documentURL: 'http://oz.test/second'",
                ]
                self.assertEqual(parse_input(lines)[1], "http://oz.test/first")

            def test_parse_input_no_data_url(self):
                self.assertEqual(parse_input(["nothing relevant"]), ("", ""))

            def test_parse_input_empty(self):
                self.assertEqual(parse_input([]), ("", ""))

        sys.exit(unittest.main())
    else:
        sys.exit(main())
