#!/usr/bin/env python

import os
import sys
import re
import json
import getopt
import requests
from pathlib import Path
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup, Tag

from bin.feed_maker_util import IO, header_str


# 데스크톱 PostView는 UA가 없으면 다른(빈) 응답을 줄 수 있어 브라우저 UA를 강제한다.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


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


def build_post_view_url(page_url: str) -> str:
    """page_url에서 blogId/logNo를 뽑아 정규 PostView URL을 만든다.

    패턴이 맞지 않으면 받은 URL을 그대로 사용한다(이미 PostView URL일 수 있음).
    """
    blog_id = None
    log_no = None
    m = re.search(r"[?&]blogId=(?P<blog_id>[^&]+)", page_url)
    if m:
        blog_id = m.group("blog_id")
    m = re.search(r"[?&]logNo=(?P<log_no>\d+)", page_url)
    if m:
        log_no = m.group("log_no")
    if blog_id and log_no:
        return f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
    return page_url


def _component_type(component: Tag) -> str:
    """se-component div의 세부 타입 class(se-text, se-image 등)를 반환."""
    for cls in component.get("class", []):
        if cls.startswith("se-") and cls not in ("se-component", "se-l-default"):
            return cls
    return ""


def _clean_inline_html(inner: str) -> str:
    """문단 inner HTML에서 span/잡다한 속성을 제거하되 a/strong/strike 등은 보존."""
    # 보존하지 않을 속성 제거(href, target은 링크 동작에 필요하므로 유지)
    inner = re.sub(r' (style|class|lang|id|onclick|data-[\w-]+)="[^"]*"', "", inner)
    inner = re.sub(r"</?span[^>]*>", "", inner)
    # 제로폭 공백(네이버가 빈 줄에 쓰는 ​) 제거
    inner = inner.replace("​", "").strip()
    return inner


def _render_text(component: Tag) -> list[str]:
    """se-text/se-quotation 등 문단 컴포넌트를 <p> 줄 목록으로 변환."""
    lines: list[str] = []
    paragraphs = component.select("p.se-text-paragraph")
    if paragraphs:
        for p in paragraphs:
            inner = _clean_inline_html(p.decode_contents())
            if inner:
                lines.append(f"<p>{inner}</p>")
    else:
        text = component.get_text(strip=True).replace("​", "").strip()
        if text:
            lines.append(f"<p>{text}</p>")
    return lines


def _render_images(component: Tag) -> list[str]:
    """se-image/se-imageGroup 컴포넌트의 이미지(+캡션)를 순서대로 변환."""
    lines: list[str] = []
    for img in component.find_all("img"):
        # 지연 로딩 이미지는 data-lazy-src에 실제 URL이 있다.
        src = img.get("data-lazy-src") or img.get("src")
        if src:
            lines.append(f"<img src='{src}'/>")
    caption = component.find(attrs={"class": "se-caption"})
    if isinstance(caption, Tag):
        caption_text = caption.get_text(strip=True)
        if caption_text:
            lines.append(f"<p>{caption_text}</p>")
    return lines


def _render_oglink(component: Tag) -> list[str]:
    """se-oglink(링크 카드)를 <a>title</a> 한 줄로 변환."""
    link = component.find("a", href=True)
    if not isinstance(link, Tag):
        return []
    href = link.get("href", "")
    title_el = component.find(attrs={"class": "se-oglink-title"})
    title = (
        title_el.get_text(strip=True)
        if isinstance(title_el, Tag)
        else link.get_text(strip=True)
    ) or href
    return [f"<p><a href='{href}'>{title}</a></p>"]


def render_content(html_text: str) -> str:
    """PostView HTML의 se-main-container를 문서 순서대로 본문/이미지 HTML로 변환.

    본문(텍스트)과 이미지가 원본에 나타난 순서를 그대로 보존하는 것이 핵심이다.
    """
    soup = BeautifulSoup(html_text, "html.parser")
    container = soup.find(attrs={"class": "se-main-container"})
    if not isinstance(container, Tag):
        return ""

    lines: list[str] = []
    for component in container.find_all(attrs={"class": "se-component"}):
        if not isinstance(component, Tag):
            continue
        ctype = _component_type(component)
        if ctype in ("se-text", "se-quotation", "se-sectionTitle"):
            lines.extend(_render_text(component))
        elif ctype in ("se-image", "se-imageGroup"):
            lines.extend(_render_images(component))
        elif ctype == "se-oglink":
            lines.extend(_render_oglink(component))
        elif ctype == "se-horizontalLine":
            lines.append("<hr/>")
        else:
            # 알 수 없는 컴포넌트는 이미지 → 텍스트 순으로 최선을 다해 추출
            lines.extend(_render_images(component))
            lines.extend(_render_text(component))

    if not lines:
        return ""
    return "<div>\n" + "\n".join(lines) + "\n</div>"


def main():
    # stdin은 추출기 결과지만 순서가 어긋나 있으므로 버리고 원문을 새로 가져온다.
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

    url = build_post_view_url(page_url)
    cookies = read_cookies(feed_dir_path)
    headers = {"User-Agent": USER_AGENT}

    if debug:
        print(f"# DEBUG request URL: {url}", file=sys.stderr)
        print(f"# DEBUG cookie keys: {sorted(cookies.keys())}", file=sys.stderr)
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=5)
        if debug:
            print(f"# DEBUG status: {response.status_code}", file=sys.stderr)
        if not debug:
            response.raise_for_status()
    except requests.RequestException as e:
        if (
            isinstance(e, requests.HTTPError)
            and e.response is not None
            and e.response.status_code in (401, 403)
        ):
            # 인증 만료/비공개 글. 시끄러운 ERROR 로그 없이 header만 내보내
            # feed_maker가 size_too_small 경로로 조용히 스킵하도록 한다.
            print(header_str)
            sys.exit(0)
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)

    if debug:
        print(response.text)
        return

    body = render_content(str(response.text))
    print(header_str)
    if body:
        print(body)


# --- tests ---

_MODULE = __name__

# 입력 HTML 스키마(골든 마스터). PostView 구조가 바뀌면 이 테스트가 깨져 알려준다.
SAMPLE_POSTVIEW_HTML = """
<html><body>
<div class="se-main-container">
  <div class="se-component se-text se-l-default">
    <div class="se-module se-module-text">
      <p class="se-text-paragraph"><span class="se-fs-fs16">​</span></p>
      <p class="se-text-paragraph"><span class="se-fs-fs16">철대제목 첫문단.</span></p>
    </div>
  </div>
  <div class="se-component se-image se-l-default">
    <div class="se-module se-module-image">
      <a href="#" class="se-module-image-link">
        <img src="https://postfiles.pstatic.net/x/first.jpg?type=w773" class="se-image-resource"/>
      </a>
    </div>
  </div>
  <div class="se-component se-text se-l-default">
    <div class="se-module se-module-text">
      <p class="se-text-paragraph"><span class="se-fs-fs16">둘째 문단 <a href="https://ex.com" target="_blank">출처</a></span></p>
    </div>
  </div>
  <div class="se-component se-image se-l-default">
    <div class="se-module se-module-image">
      <img data-lazy-src="https://postfiles.pstatic.net/x/second.png?type=w966" src="https://ssl.pstatic.net/static/blank.gif" class="se-image-resource"/>
    </div>
  </div>
</div>
</body></html>
"""


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
                ]
            )
        )
        result = read_cookies(self.tmp)
        self.assertEqual(result, {"NID_AUT": "aut_val", "NID_SES": "ses_val"})

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
        self.assertEqual(read_cookies(self.tmp), {})

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)


class TestBuildPostViewUrl(unittest.TestCase):
    def test_builds_canonical_url(self):
        self.assertEqual(
            build_post_view_url(
                "http://blog.naver.com/PostView.naver?blogId=ranto28&logNo=224327635026"
            ),
            "https://blog.naver.com/PostView.naver?blogId=ranto28&logNo=224327635026",
        )

    def test_passthrough_when_no_match(self):
        self.assertEqual(
            build_post_view_url("https://example.com/foo"), "https://example.com/foo"
        )


class TestRenderContent(unittest.TestCase):
    def test_preserves_text_image_order(self):
        body = render_content(SAMPLE_POSTVIEW_HTML)
        order = [
            "text" if line.startswith("<p>") else "img"
            for line in body.splitlines()
            if line.startswith(("<p>", "<img"))
        ]
        # 텍스트 -> 이미지 -> 텍스트 -> 이미지 순서가 보존되어야 한다.
        # (첫 컴포넌트의 빈 문단은 제거되므로 텍스트 1줄만 남는다)
        self.assertEqual(order, ["text", "img", "text", "img"])

    def test_drops_empty_paragraphs(self):
        body = render_content(SAMPLE_POSTVIEW_HTML)
        self.assertNotIn("<p></p>", body)
        self.assertNotIn("​", body)

    def test_preserves_inline_anchor(self):
        body = render_content(SAMPLE_POSTVIEW_HTML)
        self.assertIn('<a href="https://ex.com" target="_blank">출처</a>', body)

    def test_uses_lazy_src_when_present(self):
        body = render_content(SAMPLE_POSTVIEW_HTML)
        self.assertIn(
            "<img src='https://postfiles.pstatic.net/x/second.png?type=w966'/>", body
        )
        self.assertNotIn("blank.gif", body)

    def test_empty_when_no_container(self):
        self.assertEqual(render_content("<html><body>nope</body></html>"), "")


class TestInputSchema(unittest.TestCase):
    def test_postview_structure_is_unchanged(self):
        """PostView HTML이 의존하는 구조 셀렉터가 유지되는지 검증."""
        soup = BeautifulSoup(SAMPLE_POSTVIEW_HTML, "html.parser")
        container = soup.find(attrs={"class": "se-main-container"})
        assert isinstance(container, Tag)
        self.assertTrue(container.find_all(attrs={"class": "se-component"}))
        self.assertTrue(container.select("p.se-text-paragraph"))
        self.assertTrue(container.find("img"))


class TestMainFetch(unittest.TestCase):
    def _mock_response(self, text, status=200):
        resp = unittest.mock.MagicMock()
        resp.status_code = status
        resp.text = text
        resp.raise_for_status = unittest.mock.MagicMock()
        return resp

    def test_renders_body_in_order(self):
        import io
        import contextlib

        buf = io.StringIO()
        with (
            patch(f"{_MODULE}.read_cookies", return_value={"NID_AUT": "a"}),
            patch(
                f"{_MODULE}.requests.get",
                return_value=self._mock_response(SAMPLE_POSTVIEW_HTML),
            ) as mock_get,
            patch(f"{_MODULE}.IO.read_stdin"),
            contextlib.redirect_stdout(buf),
        ):
            sys.argv = [
                "prog",
                "-f",
                "/some/path",
                "http://blog.naver.com/PostView.naver?blogId=ranto28&logNo=123",
            ]
            main()
        out = buf.getvalue()
        # 정규 URL과 UA/cookie가 전달되는지
        args, kwargs = mock_get.call_args
        self.assertEqual(
            args[0],
            "https://blog.naver.com/PostView.naver?blogId=ranto28&logNo=123",
        )
        self.assertIn("User-Agent", kwargs["headers"])
        self.assertEqual(kwargs["cookies"], {"NID_AUT": "a"})
        # 첫 이미지가 둘째 텍스트보다 먼저 나와야 한다(순서 보존).
        self.assertLess(out.index("first.jpg"), out.index("둘째 문단"))

    def test_403_emits_header_only_and_exits_zero(self):
        from io import StringIO

        http_err = requests.HTTPError("403 Forbidden")
        http_err.response = unittest.mock.MagicMock(status_code=403)
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
            sys.argv = ["prog", "http://blog.naver.com/PostView.naver?blogId=b&logNo=1"]
            with self.assertRaises(SystemExit) as cm:
                main()
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(err_buf.getvalue(), "")
        self.assertEqual(out_buf.getvalue().strip(), header_str.strip())

    def test_non_auth_http_error_reports_error(self):
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
            sys.argv = ["prog", "http://blog.naver.com/PostView.naver?blogId=b&logNo=1"]
            with self.assertRaises(SystemExit) as cm:
                main()
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Error fetching URL", err_buf.getvalue())


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner().run(suite)


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        run_tests()
    else:
        sys.exit(main())
