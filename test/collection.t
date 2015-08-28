#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import subprocess
import feedmakerutil


class CollectionTest(unittest.TestCase):

	def test_daum_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "daum.webtoon.2.conf.xml"
		fileNamePrefix = "daum.webtoon.2.list"
		htmlFileName = fileNamePrefix + ".html"
		extractedFileName = fileNamePrefix + ".extracted"
		listFileName = fileNamePrefix + ".txt"

		expected = feedmakerutil.readFile(extractedFileName)
		cmd = "cat %s | extract_element.py collection" % (htmlFileName)
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)

		expected = feedmakerutil.readFile(listFileName)
		cmd = "cat %s | %s/daum/capture_item_daumwebtoon_mobile.pl" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)


	def test_kakao_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "kakao.webtoon.2.conf.xml"
		fileNamePrefix = "kakao.webtoon.2.list"
		htmlFileName = fileNamePrefix + ".html"
		extractedFileName = fileNamePrefix + ".extracted"
		listFileName = fileNamePrefix + ".txt"

		expected = feedmakerutil.readFile(extractedFileName)
		cmd = "cat %s | extract_element.py collection" % (htmlFileName)
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)

		expected = feedmakerutil.readFile(listFileName)
		cmd = "cat %s | %s/kakao/capture_item_kakaowebtoon.pl" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)


	def test_naver_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "naver.webtoon.2.conf.xml"
		fileNamePrefix = "naver.webtoon.2.list"
		htmlFileName = fileNamePrefix + ".html"
		extractedFileName = fileNamePrefix + ".extracted"
		listFileName = fileNamePrefix + ".txt"

		expected = feedmakerutil.readFile(extractedFileName)
		cmd = "cat %s | extract_element.py collection" % (htmlFileName)
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)

		expected = feedmakerutil.readFile(listFileName)
		cmd = "cat %s | %s/naver/capture_item_naverwebtoon.pl" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)


	def test_naver_cast(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "naver.cast.1.conf.xml"
		fileNamePrefix = "naver.cast.1.list"
		htmlFileName = fileNamePrefix + ".html"
		extractedFileName = fileNamePrefix + ".extracted"
		listFileName = fileNamePrefix + ".txt"

		expected = feedmakerutil.readFile(extractedFileName)
		cmd = "cat %s | extract_element.py collection" % (htmlFileName)
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)

		expected = feedmakerutil.readFile(listFileName)
		cmd = "cat %s | %s/naver/capture_item_navercastpc.pl" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)


	def test_naver_blog(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "naver.blog.1.conf.xml"
		fileNamePrefix = "naver.blog.1.list"
		htmlFileName = fileNamePrefix + ".html"
		extractedFileName = fileNamePrefix + ".extracted"
		listFileName = fileNamePrefix + ".txt"

		expected = feedmakerutil.readFile(extractedFileName)
		cmd = "cat %s | extract_element.py collection" % (htmlFileName)
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)

		expected = feedmakerutil.readFile(listFileName)
		cmd = "cat %s | %s/naver/capture_item_naverblog.pl" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)


	def test_ollehmarket_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "ollehmarket.webtoon.2.conf.xml"
		fileNamePrefix = "ollehmarket.webtoon.2.list"
		htmlFileName = fileNamePrefix + ".html"
		extractedFileName = fileNamePrefix + ".extracted"
		listFileName = fileNamePrefix + ".txt"

		expected = feedmakerutil.readFile(extractedFileName)
		cmd = "cat %s | extract_element.py collection" % (htmlFileName)
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)

		expected = feedmakerutil.readFile(listFileName)
		cmd = "cat %s | %s/ollehmarket/capture_item_ollehmarketwebtoon.pl" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)


	def test_yonginlib(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "yonginlib.1.conf.xml"
		fileNamePrefix = "yonginlib.1.list"
		htmlFileName = fileNamePrefix + ".html"
		extractedFileName = fileNamePrefix + ".extracted"
		listFileName = fileNamePrefix + ".txt"

		expected = feedmakerutil.readFile(extractedFileName)
		cmd = "cat %s | extract_element.py collection" % (htmlFileName)
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)

		expected = feedmakerutil.readFile(listFileName)
		cmd = "cat %s | %s/yonginlib/capture_item_yonginlib.pl" % (extractedFileName, os.environ['FEED_MAKER_CWD'])
		result = feedmakerutil.execCmd(cmd)
		self.assertEqual(expected, result)


if __name__ == "__main__":
	unittest.main()
