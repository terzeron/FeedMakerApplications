#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import subprocess
import feedmakerutil


class CollectionTest(unittest.TestCase):

    def test_daum_webtoon(self):
        os.putenv("FEED_MAKER_CONF_FILE", "daum.webtoon.2.conf.xml")
        fileNamePrefix = "daum.webtoon.2.list"
        htmlFileName = fileNamePrefix + ".html"
        extractedFileName = fileNamePrefix + ".extracted"
        listFileName = fileNamePrefix + ".txt"

        expected = feedmakerutil.read_file(extractedFileName)
        cmd = "cat %s | extract_element.py collection" % (htmlFileName)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)

        expected = feedmakerutil.read_file(listFileName)
        cmd = "cat %s | %s/daum/capture_item_daumwebtoon.py" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)


    def test_kakao_webtoon(self):
        os.putenv("FEED_MAKER_CONF_FILE", "kakao.webtoon.2.conf.xml")
        fileNamePrefix = "kakao.webtoon.2.list"
        htmlFileName = fileNamePrefix + ".html"
        extractedFileName = fileNamePrefix + ".extracted"
        listFileName = fileNamePrefix + ".txt"

        expected = feedmakerutil.read_file(extractedFileName)
        cmd = "cat %s | extract_element.py collection" % (htmlFileName)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)

        expected = feedmakerutil.read_file(listFileName)
        cmd = "cat %s | %s/kakao/capture_item_kakaowebtoon.py" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
        print(cmd)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)


    def test_naver_webtoon(self):
        os.putenv("FEED_MAKER_CONF_FILE", "naver.webtoon.2.conf.xml")
        fileNamePrefix = "naver.webtoon.2.list"
        htmlFileName = fileNamePrefix + ".html"
        extractedFileName = fileNamePrefix + ".extracted"
        listFileName = fileNamePrefix + ".txt"

        expected = feedmakerutil.read_file(extractedFileName)
        cmd = "cat %s | extract_element.py collection" % (htmlFileName)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)

        expected = feedmakerutil.read_file(listFileName)
        cmd = "cat %s | %s/naver/capture_item_naverwebtoon.py" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)


    def test_naver_cast(self):
        os.putenv("FEED_MAKER_CONF_FILE", "naver.cast.1.conf.xml")
        fileNamePrefix = "naver.cast.1.list"
        htmlFileName = fileNamePrefix + ".html"
        extractedFileName = fileNamePrefix + ".extracted"
        listFileName = fileNamePrefix + ".txt"

        expected = feedmakerutil.read_file(extractedFileName)
        cmd = "cat %s | extract_element.py collection" % (htmlFileName)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)

        expected = feedmakerutil.read_file(listFileName)
        cmd = "cat %s | %s/naver/capture_item_navercastpc.py" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)


    def test_naver_blog(self):
        os.putenv("FEED_MAKER_CONF_FILE", "naver.blog.1.conf.xml")
        fileNamePrefix = "naver.blog.1.list"
        htmlFileName = fileNamePrefix + ".html"
        extractedFileName = fileNamePrefix + ".extracted"
        listFileName = fileNamePrefix + ".txt"

        expected = feedmakerutil.read_file(extractedFileName)
        cmd = "cat %s | extract_element.py collection" % (htmlFileName)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)

        expected = feedmakerutil.read_file(listFileName)
        cmd = "cat %s | %s/naver/capture_item_naverblog.py" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)


    def test_ollehmarket_webtoon(self):
        os.putenv("FEED_MAKER_CONF_FILE", "ollehmarket.webtoon.2.conf.xml")
        fileNamePrefix = "ollehmarket.webtoon.2.list"
        htmlFileName = fileNamePrefix + ".html"
        extractedFileName = fileNamePrefix + ".extracted"
        listFileName = fileNamePrefix + ".txt"

        expected = feedmakerutil.read_file(extractedFileName)
        cmd = "cat %s | extract_element.py collection" % (htmlFileName)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)

        expected = feedmakerutil.read_file(listFileName)
        cmd = "cat %s | %s/ollehmarket/capture_item_ollehmarketwebtoon.py" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)


    def test_yonginlib(self):
        os.putenv("FEED_MAKER_CONF_FILE", "yonginlib.1.conf.xml")
        fileNamePrefix = "yonginlib.1.list"
        htmlFileName = fileNamePrefix + ".html"
        extractedFileName = fileNamePrefix + ".extracted"
        listFileName = fileNamePrefix + ".txt"

        expected = feedmakerutil.read_file(extractedFileName)
        cmd = "cat %s | extract_element.py collection" % (htmlFileName)
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)

        expected = feedmakerutil.read_file(listFileName)
        cmd = "cat %s | %s/yonginlib/capture_item_yonginlib.py" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
        result = feedmakerutil.exec_cmd(cmd)
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
