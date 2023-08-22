#!/usr/bin/env python


import io
import os
import sys
import re
import getopt
import collections
from bin.feed_maker_util import IO


def get_next_page_url(page_content_line_list, form_name):
    state = 0
    url = "http://blog.daum.net/_blog/_articleCate_list.do?"
    for line in page_content_line_list:
        if state == 0:
            m = re.search(r'<form name="([^"]+)"', line)
            if m and m.group(1) == form_name:
                state = 1
        elif state == 1:
            if re.search(r'</form>', line):
                state = 2
            m = re.search(r'<input[^>]*name="([^"]+)" value="([^"]+)"', line)
            if m:
                if m.group(1) in ("blogid", "maxarticleno", "minarticleno", "maxregdt", "minregdt", "listScale", "dispkind", "viewKind", "before_page", "category_id", "articleno", "regdt", "CATEGORYID", "articleno"):
                    url = url + "&%s=%s" % (m.group(1), m.group(2))
        elif state == 2:
            m = re.search(r'<a class="Select">\d+</a><a href="javascript:go_page\((\d+)\)', line)
            if m:
                url = url + "&current_page=%s" % (m.group(1))
            else:
                m = re.search(r'<a class="cB_Text" href="javascript:go_page\((\d+)\)', line)
                if m:
                    url = url + "&current_page=%s" % (m.group(1))

    is_end = False
    if not re.search(r'current_page=', url):
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
            m = re.search(r'<a href="/_blog/BlogTypeView.do\?blogid=(?P<blog_id>[^&]+)&articleno=(?P<article_no>\d+)[^"]*"[^>]*title="(?P<title>[^"]+)"', line)
            if m:
                blog_id = m.group("blog_id")
                article_no = m.group("article_no")
                link = "http://blog.daum.net/_blog/hdn/_article_contentsView.do?blogid=%s&articleno=%s&looping=0&longOpen=" % (blog_id, article_no)
                title = m.group("title")
                title = re.sub(r'&quot;', '', title)
                result_list.append((link, title))
        else:
            break
    return result_list


def main():
    encoding = "utf-8"
    is_end = False
    
    num_of_recent_feeds = 30
    optlist, args = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    # get a url of first list page
    page_content_line_list = IO.read_stdin_as_line_list()
    result_list = print_article_url_list(page_content_line_list)
    next_page_url, is_end = get_next_page_url(page_content_line_list, "articleType_list")

    # get url list from first list page (iterative)
    while len(result_list) < num_of_recent_feeds:
        page_content = get_page_content(next_page_url, encoding)
        page_content_line_list = re.split(r'\n', page_content)
        result_list.extend(print_article_url_list(page_content_line_list))
        next_page_url, is_end = get_next_page_url(page_content_line_list, "cate_list")
        if is_end:
            break

    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))

            
if __name__ == "__main__":
    sys.exit(main())
        
