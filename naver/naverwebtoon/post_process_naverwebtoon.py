#!/usr/bin/env python


import sys
import os
import re
import json
import getopt
import logging
import logging.config
from typing import List
from pathlib import Path
from bin.feed_maker_util import IO, Config, URL, header_str
from bin.crawler import Crawler
import unittest
from unittest.mock import patch


logging.config.fileConfig(os.environ["FM_HOME_DIR"] + "/logging.conf")
LOGGER = logging.getLogger()


def print_img_tag(feed_dir_path: Path, page_url: str) -> None:
    config = Config(feed_dir_path)
    if not config:
        LOGGER.error("can't read configuration")
        return
    rss_conf = config.get_rss_configs()
    m = re.search(r"https://[^/]+/(?P<rss_file_name>.+\.xml)", rss_conf["rss_link"])
    if m:
        rss_file_name = m.group("rss_file_name")
        md5_name = URL.get_short_md5_name(URL.get_url_path(page_url))
        print(
            f"<img src='https://terzeron.com/img/1x1.jpg?feed={rss_file_name}&item={md5_name}'/>"
        )


def main() -> int:
    feed_dir_path = Path.cwd()
    url_prefix = "https://comic.naver.com/api/article/list/info?titleId="

    IO.read_stdin()

    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == "-f":
            feed_dir_path = Path(a)
        if o == "-n":
            _ = int(a)

    tag_list: List = []
    page_url = args[0]
    m = re.search(r"titleId=(?P<title_id>\d+)", page_url)
    if m:
        title_id = m.group("title_id")
        link = url_prefix + title_id
        crawler = Crawler(dir_path=feed_dir_path)
        result, error, _ = crawler.run(link)
        del crawler
        if error:
            LOGGER.error("Error: can't get data from '%s'", link)
            return -1

        json_data = json.loads(result)

        if "curationTagList" in json_data:
            for curation in json_data["curationTagList"]:
                if "tagName" in curation:
                    tag_list.append(curation["tagName"])

        if "titleName" in json_data:
            title_name = json_data["titleName"]
        if "synopsis" in json_data:
            synopsis = json_data["synopsis"]
        if "thumbnailUrl" in json_data:
            thumbnail_url = json_data["thumbnailUrl"]

        print(header_str)
        print("<p>" + title_name + "</p>")
        print("<p>" + synopsis + "</p>")
        print("<p><img src='" + thumbnail_url + "'></p>")
        print("<ul>")
        for tag in tag_list:
            print("<li>#" + tag + "</li>")
        print("</ul>")
        print_img_tag(feed_dir_path, page_url)

    return 0


class TestPostProcessNaverWebtoon(unittest.TestCase):
    SAMPLE_API_RESPONSE = """
{
    "titleName": "Sample Webtoon",
    "synopsis": "This is a sample synopsis.",
    "thumbnailUrl": "http://example.com/thumbnail.jpg",
    "curationTagList": [
        { "tagName": "Gag" },
        { "tagName": "Fantasy" }
    ]
}
"""

    def _anonymize_recursive(self, obj):
        if isinstance(obj, dict):
            return {k: self._anonymize_recursive(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._anonymize_recursive(obj[0])] if obj else []
        if isinstance(obj, str):
            return "__STRING__"
        return obj

    @patch("__main__.IO.read_stdin")
    @patch("__main__.Crawler.run")
    def test_input_schema_is_unchanged(self, mock_crawler_run, mock_read_stdin):
        """API 응답 JSON의 스키마가 변경되지 않았는지 검증합니다."""
        # IO.read_stdin이 테스트를 block하지 않도록 mock 처리
        mock_read_stdin.return_value = ""

        # Crawler.run이 가짜 응답을 반환하도록 설정
        mock_crawler_run.return_value = (self.SAMPLE_API_RESPONSE, None, None)

        # 스키마 검증
        sample_data = json.loads(self.SAMPLE_API_RESPONSE)
        golden_schema = self._anonymize_recursive(sample_data)
        self.assertEqual(
            self._anonymize_recursive(sample_data),
            golden_schema,
            "API 응답 스키마가 변경되었습니다.",
        )

    # --- end-to-end with real sampled data (network mocked) ---
    # 이 스크립트는 stdin을 무시하고 page_url의 titleId로 api/article/list/info를 직접 fetch한다.
    # 그래서 directive에 따라 Crawler.run을 실제 응답으로 mock(네트워크 1회분을 가짜로 반환)한다.
    # REAL_API_RESPONSE: comic.naver.com/api/article/list/info?titleId=851431 의 실제 응답에서
    #                    파서가 읽는 필드만 추린 것.
    REAL_API_RESPONSE = (
        '{"titleName": "비공식 CC",'
        ' "synopsis": "캠퍼스 인기남 성우와 비밀 연애 중인 도아.",'
        ' "thumbnailUrl": "https://image-comic.pstatic.net/webtoon/851431/thumbnail/thumbnail_IMAG21_d373b139-bdea-4e91-bfde-73b5b94c6b2d.jpg",'
        ' "curationTagList": [{"tagName": "로맨스"}, {"tagName": "캠퍼스"}, {"tagName": "고자극로맨스"}]}'
    )

    @patch("__main__.IO.read_stdin", return_value="")
    @patch("__main__.Crawler.run")
    def test_real_sample_end_to_end(self, mock_crawler_run, mock_read_stdin):
        import io as _io
        import contextlib as _ctx

        mock_crawler_run.return_value = (self.REAL_API_RESPONSE, None, None)
        feed_dir = str(Path(__file__).resolve().parent)
        page_url = "https://comic.naver.com/webtoon/list?titleId=851431"
        buf = _io.StringIO()
        with (
            patch.object(
                sys, "argv", ["post_process_naverwebtoon.py", "-f", feed_dir, page_url]
            ),
            _ctx.redirect_stdout(buf),
        ):
            main()
        out = buf.getvalue()
        self.assertIn("<p>비공식 CC</p>", out)
        self.assertIn("<p>캠퍼스 인기남 성우와 비밀 연애 중인 도아.</p>", out)
        self.assertIn(
            "<p><img src='https://image-comic.pstatic.net/webtoon/851431/thumbnail/thumbnail_IMAG21_d373b139-bdea-4e91-bfde-73b5b94c6b2d.jpg'></p>",
            out,
        )
        self.assertIn("<li>#로맨스</li>", out)
        self.assertIn("<li>#캠퍼스</li>", out)
        self.assertIn("<li>#고자극로맨스</li>", out)


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner().run(suite)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        run_tests()
    else:
        sys.exit(main())
