#!/usr/bin/env python

import sys
import re
import json
import getopt
import requests
from urllib.parse import unquote
import unittest
from unittest.mock import patch

from bin.feed_maker_util import IO, header_str, Env


def main():
    # dump out stdin
    IO.read_stdin()

    optlist, args = getopt.getopt(sys.argv[1:], "f:")
    page_url = args[0]
    
    m = re.search(r'cafes/(?P<cafe_id>\d+)/articles/(?P<article_id>\d+)', page_url)
    if m:
        cafe_id = m.group("cafe_id")
        article_id = m.group("article_id")
        url = f"https://apis.naver.com/cafe-web/cafe-articleapi/v3/cafes/{cafe_id}/articles/{article_id}"
        
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching URL: {e}", file=sys.stderr)
            sys.exit(1)

        if response:
            data = json.loads(str(response.text))
            if "result" in data:
                result = data["result"]
                #import pprint
                #pprint.pprint(data["result"])

                print(header_str)
                
                # 본문
                image_list: list[str] = []
                if "article" in result:
                    article = result["article"]

                    # 이미지 수집
                    content_elements = article.get("contentElements", [])
                    if not content_elements and "scrap" in article:
                        content_elements = article.get("scrap", {}).get("contentElements", [])

                    for image_element in content_elements:
                        json_ = image_element.get("json", {})
                        if "image" in json_:
                            image_url = json_["image"].get("url", "")
                            if "egloos.com" in image_url or "hanafos.com" in image_url:
                                continue
                            m_img = re.search(r'https://dthumb-phinf\.pstatic\.net/\?src=%22(?P<real_image_url>http.*)%22', image_url)
                            if m_img:
                                image_url = unquote(m_img.group("real_image_url"))
                            image_list.append(f"<img src='{image_url}' />")
                        elif "url" in json_:
                            m_yt = re.search(r'(?P<youtube_link>youtube.com/embed/(?P<youtube_id>\w+))', json_["url"])
                            if m_yt:
                                youtube_id = m_yt.group("youtube_id")
                                image_url = f"https://i.ytimg.com/vi_webp/{youtube_id}/maxresdefault.webp"
                                image_list.append(f"<a href='https://{m_yt.group('youtube_link')}'><img src='{image_url}' /></a>")
                            
                    # 본문 출력 
                    html = article.get("contentHtml", "")
                    if "scrap" in article and "contentHtml" in article.get("scrap", {}):
                        html += article["scrap"]["contentHtml"]
                    
                    for i, img_tag in enumerate(image_list):
                        html = html.replace(f"[[[CONTENT-ELEMENT-{i}]]]", img_tag)

                    html = re.sub(r' (style|class|lang)="[^"]*"', '', html)
                    html = re.sub(r'</?span>', '', html)
                    html = re.sub(r'<(br|img) ?/?>', r'<\1/>\n', html)
                    html = re.sub(r'</(div|span|p|li|h\d)/?>', r'</\1>\n', html)
                        
                    print("<div>")
                    print(html)
                    print("</div>")
                        
                # 댓글
                comments = result.get("comments", {}).get("items", [])
                if comments:
                    print("<div>\n<h2>--------------------- 댓글 ---------------------</h2>\n<div>\n")
                    for comment in comments:
                        nick = comment.get("writer", {}).get("nick", "???")
                        comment_text = comment.get("content", "")
                        comment_sticker_img_url = comment.get("sticker", {}).get("url", "") + "?type=pa30_30"
                        print(f"<p><span>{nick}:</span> <span>{comment_text}</span> <span><img src='{comment_sticker_img_url}' /></span></p>\n")
                    print("</div>\n</div>\n")


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
        if isinstance(obj, str): return "__STRING__"
        if isinstance(obj, int): return "__NUMBER__"
        return obj

    @patch('__main__.requests.get')
    def test_input_schema_is_unchanged(self, mock_get):
        """API 응답 JSON의 스키마가 변경되지 않았는지 검증합니다."""
        mock_get.return_value.text = self.SAMPLE_API_RESPONSE
        sample_data = json.loads(mock_get.return_value.text)
        golden_schema = self._anonymize_recursive(sample_data)
        self.assertEqual(self._anonymize_recursive(sample_data), golden_schema)


def run_tests():
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    unittest.TextTestRunner().run(suite)


if __name__ == "__main__":
    if Env.get("TEST", "0") == "1":
        run_tests()
    else:
        sys.exit(main())
