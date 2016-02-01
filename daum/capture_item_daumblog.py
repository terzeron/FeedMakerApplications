#!/usr/bin/env python3


import io
import os
import sys
import re
import feedmakerutil


def getNextPageUrl(pageContentLineList, formName):
    state = 0
    url = "http://blog.daum.net/_blog/ArticleCateList.do?"
    for line in pageContentLineList:
        if state == 0:
            m = re.search(r'<form name="([^"]+)"', line)
            if m and m.group(1) == formName:
                state = 1
        elif state == 1:
            if re.search(r'</form>', line):
                state = 2
            m = re.search(r'<input[^>]*name="([^"]+)" value="([^"]+)"', line)
            if m:
                if m.group(1) in ("blogid", "maxarticleno", "minarticleno", "maxregdt", "minregdt", "listScale", "dispkind", "viewKind", "beforePage", "categoryId", "articleno", "regdt", "CATEGORYID", "articleno"):
                    url = url + "&%s=%s" % (m.group(1), m.group(2))
        elif state == 2:
            m = re.search(r'<a class="Select">\d+</a><a href="javascript:goPage\((\d+)\)', line)
            if m:
                url = url + "&currentPage=%s" % (m.group(1))
            else:
                m = re.search(r'<a class="cB_Text" href="javascript:goPage\((\d+)\)', line)
                if m:
                    url = url + "&currentPage=%s" % (m.group(1))

    isEnd = False
    if not re.search(r'currentPage=', url):
        isEnd = True
    return url, isEnd


def getPageContent(url, encoding):
    import urllib.request
    pageContent = ""
    with urllib.request.urlopen(url) as f:
        pageContent = f.read().decode(encoding)
    return pageContent


def printArticleUrlList(pageContentLineList):
    state = 0
    for line in pageContentLineList:
        if state == 0:
            if re.search(r'class="contArea"', line):
                state = 1
        elif state == 1:
            if re.search(r'id="pagingBox"', line):
                state = 2
            m = re.search(r'<a href="/_blog/BlogTypeView.do\?blogid=(?P<blogId>[^&]+)&articleno=(?P<articleNo>\d+)[^"]*"[^>]*title="(?P<title>[^"]+)"', line)
            if m:
                blogId = m.group("blogId")
                articleNo = m.group("articleNo")
                url = "http://blog.daum.net/_blog/hdn/ArticleContentsView.do?blogid=%s&articleno=%s&looping=0&longOpen=" % (blogId, articleNo)
                title = m.group("title")
                title = re.sub(r'&quot;', '', title)
                print("%s\t%s" % (url, title))
        else:
            break

def main():
    encoding = "utf-8"
    isEnd = False
    
    # get a url of first list page
    pageContentLineList = feedmakerutil.readStdinAsLineList()
    printArticleUrlList(pageContentLineList)
    nextPageUrl, isEnd = getNextPageUrl(pageContentLineList, "articleTypeList")
    
    # get url list from first list page (iterative)
    while True:
        pageContent = getPageContent(nextPageUrl, encoding)
        pageContentLineList = re.split(r'\n', pageContent)
        printArticleUrlList(pageContentLineList)
        nextPageUrl, isEnd = getNextPageUrl(pageContentLineList, "cateList")
        if isEnd:
            break

        
            
if __name__ == "__main__":
    main()
        
