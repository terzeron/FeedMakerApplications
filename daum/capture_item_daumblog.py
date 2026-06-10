#!/usr/bin/env python


import os
import sys
import re
import getopt
from typing import List
from bin.feed_maker_util import IO


def parse_args(argv: List[str]) -> int:
    """명령행 인자를 파싱해 최근 피드 개수를 반환."""
    num_of_recent_feeds = 30
    optlist, _ = getopt.getopt(argv, "f:n:")
    for o, a in optlist:
        if o == "-n":
            num_of_recent_feeds = int(a)
    return num_of_recent_feeds


def get_next_page_url(page_content_line_list, form_name):
    state = 0
    url = "http://blog.daum.net/_blog/_articleCate_list.do?"
    for line in page_content_line_list:
        if state == 0:
            m = re.search(r'<form name="([^"]+)"', line)
            if m and m.group(1) == form_name:
                state = 1
        elif state == 1:
            if re.search(r"</form>", line):
                state = 2
            m = re.search(r'<input[^>]*name="([^"]+)" value="([^"]+)"', line)
            if m:
                if m.group(1) in (
                    "blogid",
                    "maxarticleno",
                    "minarticleno",
                    "maxregdt",
                    "minregdt",
                    "listScale",
                    "dispkind",
                    "viewKind",
                    "before_page",
                    "category_id",
                    "articleno",
                    "regdt",
                    "CATEGORYID",
                    "articleno",
                ):
                    url = url + "&%s=%s" % (m.group(1), m.group(2))
        elif state == 2:
            m = re.search(
                r'<a class="Select">\d+</a><a href="javascript:go_page\((\d+)\)', line
            )
            if m:
                url = url + "&current_page=%s" % (m.group(1))
            else:
                m = re.search(
                    r'<a class="cB_Text" href="javascript:go_page\((\d+)\)', line
                )
                if m:
                    url = url + "&current_page=%s" % (m.group(1))

    is_end = False
    if not re.search(r"current_page=", url):
        is_end = True
    return url, is_end


def get_page_content(url, encoding):
    import urllib.request

    page_content = ""
    with urllib.request.urlopen(url) as f:
        page_content = f.read().decode(encoding)
    return page_content


def print_article_url_list(page_content_line_list):
    state = 0
    result_list = []
    for line in page_content_line_list:
        if state == 0:
            if re.search(r'class="contArea"', line):
                state = 1
        elif state == 1:
            if re.search(r'id="pagingBox"', line):
                state = 2
            m = re.search(
                r'<a href="/_blog/BlogTypeView.do\?blogid=(?P<blog_id>[^&]+)&articleno=(?P<article_no>\d+)[^"]*"[^>]*title="(?P<title>[^"]+)"',
                line,
            )
            if m:
                blog_id = m.group("blog_id")
                article_no = m.group("article_no")
                link = (
                    "http://blog.daum.net/_blog/hdn/_article_contentsView.do?blogid=%s&articleno=%s&looping=0&longOpen="
                    % (blog_id, article_no)
                )
                title = m.group("title")
                title = re.sub(r"&quot;", "", title)
                result_list.append((link, title))
        else:
            break
    return result_list


def main():
    encoding = "utf-8"
    is_end = False

    num_of_recent_feeds = parse_args(sys.argv[1:])

    # get a url of first list page
    page_content_line_list = IO.read_stdin_as_line_list()
    result_list = print_article_url_list(page_content_line_list)
    next_page_url, is_end = get_next_page_url(
        page_content_line_list, "articleType_list"
    )

    # get url list from first list page (iterative)
    while len(result_list) < num_of_recent_feeds:
        page_content = get_page_content(next_page_url, encoding)
        page_content_line_list = re.split(r"\n", page_content)
        result_list.extend(print_article_url_list(page_content_line_list))
        next_page_url, is_end = get_next_page_url(page_content_line_list, "cate_list")
        if is_end:
            break

    for link, title in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestCaptureItemDaumblog(unittest.TestCase):
            # --- parse_args ---

            def test_parse_args_default(self):
                self.assertEqual(parse_args([]), 30)

            def test_parse_args_num(self):
                self.assertEqual(parse_args(["-n", "5"]), 5)

            def test_parse_args_f_ignored(self):
                self.assertEqual(parse_args(["-f", "."]), 30)

            # --- get_next_page_url ---

            def test_get_next_page_url_collects_inputs_and_paging(self):
                lines = [
                    '<form name="articleType_list">',
                    '<input name="blogid" value="abc">',
                    '<input name="articleno" value="123">',
                    "</form>",
                    '<a class="Select">2</a><a href="javascript:go_page(3)">',
                ]
                url, is_end = get_next_page_url(lines, "articleType_list")
                self.assertEqual(
                    url,
                    "http://blog.daum.net/_blog/_articleCate_list.do?"
                    "&blogid=abc&articleno=123&current_page=3",
                )
                self.assertFalse(is_end)

            def test_get_next_page_url_cb_text_paging(self):
                lines = [
                    '<form name="cate_list">',
                    "</form>",
                    '<a class="cB_Text" href="javascript:go_page(7)">',
                ]
                url, is_end = get_next_page_url(lines, "cate_list")
                self.assertTrue(url.endswith("&current_page=7"))
                self.assertFalse(is_end)

            def test_get_next_page_url_is_end_when_no_paging(self):
                lines = ['<form name="cate_list">', "</form>"]
                url, is_end = get_next_page_url(lines, "cate_list")
                self.assertTrue(is_end)

            def test_get_next_page_url_ignores_other_form(self):
                lines = [
                    '<form name="other">',
                    '<input name="blogid" value="abc">',
                    "</form>",
                ]
                url, is_end = get_next_page_url(lines, "cate_list")
                self.assertEqual(
                    url, "http://blog.daum.net/_blog/_articleCate_list.do?"
                )
                self.assertTrue(is_end)

            # --- print_article_url_list ---

            def test_print_article_url_list_basic(self):
                lines = [
                    '<div class="contArea">',
                    '<a href="/_blog/BlogTypeView.do?blogid=myid&articleno=42&x=1" '
                    'class="c" title="My &quot;Title&quot;">',
                    '<div id="pagingBox">',
                ]
                self.assertEqual(
                    print_article_url_list(lines),
                    [
                        (
                            "http://blog.daum.net/_blog/hdn/_article_contentsView.do?"
                            "blogid=myid&articleno=42&looping=0&longOpen=",
                            "My Title",
                        )
                    ],
                )

            def test_print_article_url_list_requires_cont_area(self):
                # contArea 마커 이전의 anchor는 무시된다
                lines = [
                    '<a href="/_blog/BlogTypeView.do?blogid=x&articleno=1" title="T">',
                ]
                self.assertEqual(print_article_url_list(lines), [])

            def test_print_article_url_list_empty(self):
                self.assertEqual(print_article_url_list([]), [])

        sys.exit(unittest.main())
    else:
        sys.exit(main())
