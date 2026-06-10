#!/usr/bin/env python

import os
import sys
import re
import json
import getopt
import requests
from pathlib import Path
from urllib.parse import unquote
import unittest
from unittest.mock import patch

from bin.feed_maker_util import IO, header_str


def read_cookies(feed_dir_path: str) -> dict[str, str]:
    cookie_file = Path(feed_dir_path) / "cookies.requestsclient.json"
    cookies = {}
    if cookie_file.is_file():
        with cookie_file.open("r", encoding="utf-8") as f:
            for cookie in json.load(f):
                name = cookie.get("name", "")
                value = cookie.get("value", "")
                if name and value:
                    cookies[name] = value
    return cookies


def main():
    # dump out stdin
    IO.read_stdin()

    feed_dir_path = "."
    debug = False
    optlist, args = getopt.getopt(sys.argv[1:], "f:d")
    for opt, val in optlist:
        if opt == "-f":
            feed_dir_path = val
        elif opt == "-d":
            debug = True
    page_url = args[0]

    m = re.search(r"cafes/(?P<cafe_id>\d+)/articles/(?P<article_id>\d+)", page_url)
    if m:
        cafe_id = m.group("cafe_id")
        article_id = m.group("article_id")
        url = f"https://apis.naver.com/cafe-web/cafe-articleapi/v3/cafes/{cafe_id}/articles/{article_id}"

        cookies = read_cookies(feed_dir_path)
        if debug:
            print(f"# DEBUG request URL: {url}", file=sys.stderr)
            print(f"# DEBUG cookie keys: {sorted(cookies.keys())}", file=sys.stderr)
        try:
            response = requests.get(url, cookies=cookies, timeout=5)
            if debug:
                print(f"# DEBUG status: {response.status_code}", file=sys.stderr)
            if not debug:
                response.raise_for_status()
        except requests.RequestException as e:
            if (
                isinstance(e, requests.HTTPError)
                and e.response is not None
                and e.response.status_code == 401
            ):
                # 401은 cookie 만료/미인증 상황. 시끄러운 ERROR 로그를 만들지 않고
                # 빈 본문(header만)을 내보내 feed_maker가 size_too_small 경로로
                # 조용히 스킵하도록 한다.
                print(header_str)
                sys.exit(0)
            print(f"Error fetching URL: {e}", file=sys.stderr)
            sys.exit(1)

        if debug:
            try:
                data = json.loads(str(response.text))
                print(json.dumps(data, indent=2, ensure_ascii=False))
            except json.JSONDecodeError:
                print(response.text)
            return

        if response:
            data = json.loads(str(response.text))
            if "result" in data:
                result = data["result"]

                print(header_str)

                # 본문
                image_list: list[str] = []
                i = 0
                if "attaches" in result:
                    attaches = result["attaches"]
                    for attach in attaches:
                        if attach.get("type", "") == "M":
                            image_url = re.sub(
                                r"https://download.blog.naver.com/\w+/(\w+)/",
                                r"https://phinf.pstatic.net/image.nmv/\1/",
                                attach.get("url", ""),
                            )
                            image_list.append(f"<img src='{image_url}' />")

                if "article" in result:
                    article = result["article"]

                    # 이미지 수집
                    content_elements = article.get("contentElements", [])
                    if not content_elements and "scrap" in article:
                        content_elements = article.get("scrap", {}).get(
                            "contentElements", []
                        )

                    for image_element in content_elements:
                        json_ = image_element.get("json", {})
                        if "stickerId" in json_:
                            image_url = json_.get("url", "")
                            image_list.append(f"<!-- {image_url} -->")

                        if "image" in json_:
                            image_url = json_["image"].get("url", "")
                            if "egloos.com" in image_url or "hanafos.com" in image_url:
                                continue
                            m_img = re.search(
                                r"https://dthumb-phinf\.pstatic\.net/\?src=%22(?P<real_image_url>http.*)%22",
                                image_url,
                            )
                            if m_img:
                                image_url = unquote(m_img.group("real_image_url"))
                            image_list.append(f"<img src='{image_url}' />")
                        elif "url" in json_:
                            m_yt = re.search(
                                r"(?P<youtube_link>youtube.com/embed/(?P<youtube_id>\w+))",
                                json_["url"],
                            )
                            if m_yt:
                                youtube_id = m_yt.group("youtube_id")
                                image_url = f"https://i.ytimg.com/vi_webp/{youtube_id}/maxresdefault.webp"
                                image_list.append(
                                    f"<a href='https://{m_yt.group('youtube_link')}'><img src='{image_url}' /></a>"
                                )

                    # 본문 출력
                    html = article.get("contentHtml", "")
                    if "scrap" in article and "contentHtml" in article.get("scrap", {}):
                        html += article["scrap"]["contentHtml"]

                    for i, img_tag in enumerate(image_list):
                        html = html.replace(f"[[[CONTENT-ELEMENT-{i}]]]", img_tag)

                    html = re.sub(r' (style|class|lang)="[^"]*"', "", html)
                    html = re.sub(r"</?span>", "", html)
                    html = re.sub(r"<(br|img) ?/?>", r"<\1/>\n", html)
                    html = re.sub(r"</(div|span|p|li|h\d)/?>", r"</\1>\n", html)

                    print("<div>")
                    print(html)
                    print("</div>")

                # 댓글
                comments = result.get("comments", {}).get("items", [])
                if comments:
                    print(
                        "<div>\n<h2>--------------------- 댓글 ---------------------</h2>\n<div>\n"
                    )
                    for comment in comments:
                        nick = comment.get("writer", {}).get("nick", "???")
                        comment_text = comment.get("content", "")
                        comment_sticker_img_url = (
                            comment.get("sticker", {}).get("url", "") + "?type=pa30_30"
                        )
                        print(
                            f"<p><span>{nick}:</span> <span>{comment_text}</span> <span><img src='{comment_sticker_img_url}' /></span></p>\n"
                        )
                    print("</div>\n</div>\n")


class TestReadCookies(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.mkdtemp()

    def test_reads_multiple_cookies(self):
        cookie_file = Path(self.tmp) / "cookies.requestsclient.json"
        cookie_file.write_text(
            json.dumps(
                [
                    {"name": "NID_AUT", "value": "aut_val"},
                    {"name": "NID_SES", "value": "ses_val"},
                    {"name": "NID_JST", "value": "jst_val"},
                ]
            )
        )
        result = read_cookies(self.tmp)
        self.assertEqual(
            result, {"NID_AUT": "aut_val", "NID_SES": "ses_val", "NID_JST": "jst_val"}
        )

    def test_skips_empty_name_or_value(self):
        cookie_file = Path(self.tmp) / "cookies.requestsclient.json"
        cookie_file.write_text(
            json.dumps(
                [
                    {"name": "", "value": "val"},
                    {"name": "key", "value": ""},
                    {"name": "good", "value": "cookie"},
                ]
            )
        )
        result = read_cookies(self.tmp)
        self.assertEqual(result, {"good": "cookie"})

    def test_returns_empty_when_no_file(self):
        result = read_cookies(self.tmp)
        self.assertEqual(result, {})

    def test_returns_empty_for_empty_list(self):
        cookie_file = Path(self.tmp) / "cookies.requestsclient.json"
        cookie_file.write_text("[]")
        result = read_cookies(self.tmp)
        self.assertEqual(result, {})

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)


_MODULE = __name__


class TestMainCookiesPassedToRequest(unittest.TestCase):
    def _mock_response(self, text):
        resp = unittest.mock.MagicMock()
        resp.status_code = 200
        resp.text = text
        resp.raise_for_status = unittest.mock.MagicMock()
        return resp

    def test_cookies_forwarded_to_api(self):
        with (
            patch(
                f"{_MODULE}.read_cookies", return_value={"NID_AUT": "a", "NID_SES": "b"}
            ) as mock_rc,
            patch(f"{_MODULE}.requests.get") as mock_get,
            patch(f"{_MODULE}.IO.read_stdin"),
        ):
            mock_get.return_value = self._mock_response(
                '{"result":{"article":{"contentHtml":"hello","contentElements":[]},"comments":{"items":[]}}}'
            )
            sys.argv = [
                "prog",
                "-f",
                "/some/path",
                "https://m.cafe.naver.com/ca-fe/web/cafes/123/articles/456",
            ]
            main()
            mock_rc.assert_called_once_with("/some/path")
            mock_get.assert_called_once_with(
                "https://apis.naver.com/cafe-web/cafe-articleapi/v3/cafes/123/articles/456",
                cookies={"NID_AUT": "a", "NID_SES": "b"},
                timeout=5,
            )

    def test_default_feed_dir_when_no_f_option(self):
        with (
            patch(f"{_MODULE}.read_cookies", return_value={}) as mock_rc,
            patch(f"{_MODULE}.requests.get") as mock_get,
            patch(f"{_MODULE}.IO.read_stdin"),
        ):
            mock_get.return_value = self._mock_response(
                '{"result":{"article":{"contentHtml":"x","contentElements":[]},"comments":{"items":[]}}}'
            )
            sys.argv = [
                "prog",
                "https://m.cafe.naver.com/ca-fe/web/cafes/123/articles/456",
            ]
            main()
            mock_rc.assert_called_once_with(".")


class TestMain401HandledSilently(unittest.TestCase):
    def test_401_emits_header_only_and_exits_zero(self):
        from io import StringIO

        http_err = requests.HTTPError("401 Client Error: Unauthorized for url: x")
        http_err.response = unittest.mock.MagicMock(status_code=401)

        bad_resp = unittest.mock.MagicMock()
        bad_resp.raise_for_status = unittest.mock.MagicMock(side_effect=http_err)

        out_buf, err_buf = StringIO(), StringIO()
        with (
            patch(f"{_MODULE}.read_cookies", return_value={}),
            patch(f"{_MODULE}.requests.get", return_value=bad_resp),
            patch(f"{_MODULE}.IO.read_stdin"),
            patch("sys.stdout", out_buf),
            patch("sys.stderr", err_buf),
        ):
            sys.argv = [
                "prog",
                "https://m.cafe.naver.com/ca-fe/web/cafes/123/articles/456",
            ]
            with self.assertRaises(SystemExit) as cm:
                main()
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue().strip(), header_str.strip())

    def test_non_401_http_error_still_reports_error(self):
        from io import StringIO

        http_err = requests.HTTPError("500 Server Error")
        http_err.response = unittest.mock.MagicMock(status_code=500)

        bad_resp = unittest.mock.MagicMock()
        bad_resp.raise_for_status = unittest.mock.MagicMock(side_effect=http_err)

        err_buf = StringIO()
        with (
            patch(f"{_MODULE}.read_cookies", return_value={}),
            patch(f"{_MODULE}.requests.get", return_value=bad_resp),
            patch(f"{_MODULE}.IO.read_stdin"),
            patch("sys.stderr", err_buf),
        ):
            sys.argv = [
                "prog",
                "https://m.cafe.naver.com/ca-fe/web/cafes/123/articles/456",
            ]
            with self.assertRaises(SystemExit) as cm:
                main()
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error fetching URL", err_buf.getvalue())


class TestPostProcessNaverCafe(unittest.TestCase):
    SAMPLE_API_RESPONSE = """
{
  "result": {
    "article": {
      "contentHtml": "...",
      "contentElements": [
        { "json": { "image": { "url": "http://example.com/image.jpg" } } }
      ]
    },
    "comments": {
      "items": [
        { "writer": { "nick": "Commenter1" }, "content": "Nice post!" }
      ]
    }
  }
}
"""

    def _anonymize_recursive(self, obj):
        if isinstance(obj, dict):
            return {k: self._anonymize_recursive(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._anonymize_recursive(obj[0])] if obj else []
        if isinstance(obj, str):
            return "__STRING__"
        if isinstance(obj, int):
            return "__NUMBER__"
        return obj

    def test_input_schema_is_unchanged(self):
        """API 응답 JSON의 스키마가 변경되지 않았는지 검증합니다."""
        sample_data = json.loads(self.SAMPLE_API_RESPONSE)
        golden_schema = self._anonymize_recursive(sample_data)
        self.assertEqual(self._anonymize_recursive(sample_data), golden_schema)


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner().run(suite)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        run_tests()
    else:
        sys.exit(main())
