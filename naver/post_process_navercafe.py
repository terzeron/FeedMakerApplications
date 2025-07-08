#!/usr/bin/env python

import sys
import re
import json
import getopt
import requests
from bin.feed_maker_util import IO


def main():
    state = 0

    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    
    # dump out stdin
    IO.read_stdin()

    page_url = args[0]
    m = re.search(r'cafes/(?P<cafe_id>\d+)/articles/(?P<article_id>\d+)', page_url)
    if m:
        cafe_id = m.group("cafe_id")
        article_id = m.group("article_id")
        url = f"https://apis.naver.com/cafe-web/cafe-articleapi/v3/cafes/{cafe_id}/articles/{article_id}"
        response = requests.get(url)
        if response:
            data = json.loads(str(response.text))
            if "result" in data:
                result = data["result"]

                # 본문
                image_list: list[str] = []
                if "article" in result:
                    article = result["article"]

                    # 이미지 수집
                    if "contentElements" in article:
                        image_elements = article["contentElements"]
                        for image_element in image_elements:
                            image_url = image_element["json"]["image"]["url"]
                            image_list.append(f"<img src='{image_url}' />")
                            
                    # 본문 출력 
                    if "contentHtml" in article:
                        html = article["contentHtml"]
                        # 이미지 치환
                        for i in range(len(image_list)):
                            marker = f"[[[CONTENT-ELEMENT-{i}]]]"
                            html = html.replace(marker, image_list[i])
                        print("<div>")
                        print(html)
                        print("</div>")
                        
                # 댓글
                if "comments" in result:
                    comments = result["comments"]["items"]
                    print("<div>\n<p>--------------------- 댓글 ---------------------</p>\n<nl>")
                    for comment in comments:
                        nick = comment["writer"]["nick"]
                        comment_text = comment["content"]
                        print(f"<li>{nick}: {comment_text}</li>")
                    print("</nl>\n</div>")
                        
if __name__ == "__main__":
    sys.exit(main())

    
