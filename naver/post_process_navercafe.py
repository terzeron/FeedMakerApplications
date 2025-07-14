#!/usr/bin/env python

import sys
import re
import json
import getopt
import requests
from urllib.parse import unquote

from bin.feed_maker_util import IO, header_str


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

                print(header_str)
                
                # 본문
                image_list: list[str] = []
                if "article" in result:
                    article = result["article"]

                    # 이미지 수집
                    if "contentElements" in article:
                        image_elements = article["contentElements"]
                        if not image_elements:
                            if "scrap" in article:
                                scrap = article["scrap"]
                                if "contentElements" in scrap:
                                    image_elements = scrap["contentElements"]

                        for image_element in image_elements:
                            json_ = image_element["json"]
                            if "image" in json_:
                                image_url = json_["image"]["url"]
                                if "egloos.com" in image_url or "hanafos.com" in image_url:
                                    continue

                                m = re.search(r'https://dthumb-phinf\.pstatic\.net/\?src=%22(?P<real_image_url>http.*)%22', image_url)
                                if m:
                                    image_url = unquote(m.group("real_image_url"))
                                    
                                image_list.append(f"<img src='{image_url}' />")
                            elif "url" in json_:
                                m = re.search(r'(?P<youtube_link>youtube.com/embed/(?P<youtube_id>\w+))', json_["url"])
                                if m:
                                    youtube_link = m.group("youtube_link")
                                    youtube_id = m.group("youtube_id")
                                    image_url = f"https://i.ytimg.com/vi_webp/{youtube_id}/maxresdefault.webp"
                                    image_list.append(f"<a href='https://{youtube_link}'><img src='{image_url}' /></a>")
                            
                    # 본문 출력 
                    if "contentHtml" in article:
                        html = article["contentHtml"]
                        if "scrap" in article:
                            scrap = article["scrap"]
                            if "contentHtml" in scrap:
                                html += scrap["contentHtml"]
                            
                        # 이미지 치환
                        for i in range(len(image_list)):
                            marker = f"[[[CONTENT-ELEMENT-{i}]]]"
                            html = html.replace(marker, image_list[i])

                        # 클리닝
                        html = re.sub(r' (style|class|lang)="[^"]*"', '', html)
                        html = re.sub(r'</?span>', '', html)
                        html = re.sub(r'<(br|img) ?/?>', r'<\1/>\n', html)
                        html = re.sub(r'</(div|span|p|li|h\d)/?>', r'</\1>\n', html)
                            
                        print("<div>")
                        print(html)
                        print("</div>")
                        
                # 댓글
                if "comments" in result:
                    comments = result["comments"]["items"]
                    print("<div>\n<h2>--------------------- 댓글 ---------------------</h2>\n<div>\n")
                    for comment in comments:
                        nick = comment["writer"]["nick"]
                        comment_text = comment["content"]
                        print(f"<p><span>{nick}:</span> <span>{comment_text}</span></p>\n")
                    print("</div>\n</div>\n")


if __name__ == "__main__":
    sys.exit(main())
