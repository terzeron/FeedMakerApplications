#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import subprocess
import feedmakerutil


class ExtractionTest(unittest.TestCase):

	def test_daum_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "daum.webtoon.1.conf.xml"
		url = "http://cartoon.media.daum.net/m/webtoon/viewer/30086"
		htmlFileName = "daum.webtoon.1.html"
		extractedFileName = htmlFileName + ".extracted"
		processedFileName = htmlFileName + ".processed"
		downloadedFileName = htmlFileName + ".downloaded"

		# extract.py test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s extract.py '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(extractedFileName)
		self.assertEqual(expected, result)

        # post process test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s %s/daum/post_process_daumwebtoon.pl '%s'" % (extractedFileName, os.environ['FEED_MAKER_CONF_FILE'], os.environ['FEED_MAKER_CWD'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(processedFileName)
		self.assertEqual(expected, result)


	def test_kakao_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "kakao.webtoon.1.conf.xml"
		url = "http://page.kakao.com/viewer?productId=47731651"
		htmlFileName = "kakao.webtoon.1.html"
		extractedFileName = htmlFileName + ".extracted"
		processedFileName = htmlFileName + ".processed"
		downloadedFileName = htmlFileName + ".downloaded"

		# extract.py test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s extract.py '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(extractedFileName)
		self.assertEqual(expected, result)

        # post process test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s post_process_only_for_images.py '%s'" % (extractedFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(processedFileName)
		self.assertEqual(expected, result)


	def test_naver_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "naver.webtoon.1.conf.xml"
		url = "http://comic.naver.com/webtoon/detail.nhn?titleId=548870&no=118"
		htmlFileName = "naver.webtoon.1.html"
		extractedFileName = htmlFileName + ".extracted"
		processedFileName = htmlFileName + ".processed"
		downloadedFileName = htmlFileName + ".downloaded"

		# extract.py test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s extract.py '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(extractedFileName)
		self.assertEqual(expected, result)

		# post process test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s %s/naver/post_process_naverwebtoon_mobile.pl '%s'" % (extractedFileName, os.environ['FEED_MAKER_CONF_FILE'], os.environ['FEED_MAKER_CWD'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(processedFileName)
		self.assertEqual(expected, result)

		# download test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s download_image.pl '%s'" % (processedFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(downloadedFileName)
		self.assertEqual(expected, result)


	def test_naver_webtoon_ozviewer(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "naver.webtoon.3.conf.xml"
		url = "http://comic.naver.com/webtoon/detail.nhn?titleId=655277&no=9"
		htmlFileName = "naver.webtoon.3.html"
		processedFileName = htmlFileName + ".processed"
		downloadedFileName = htmlFileName + ".downloaded"

		# post process test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s %s/naver/post_process_naverwebtoon_ozviewer.pl '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], os.environ['FEED_MAKER_CWD'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(processedFileName)
		self.assertEqual(expected, result)

		# download test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s download_image.pl '%s'" % (processedFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(downloadedFileName)
		self.assertEqual(expected, result)


	def test_naver_cast(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "naver.cast.2.conf.xml"
		url = "http://navercast.naver.com/contents.nhn?contents_id=90496&leafId=2875"
		htmlFileName = "naver.cast.2.html"
		extractedFileName = htmlFileName + ".extracted"

		# extract.py test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s extract.py '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(extractedFileName)
		self.assertEqual(expected, result)


	def test_naver_blog(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "naver.blog.1.conf.xml"
		url = "http://blog.naver.com/PostView.nhn?blogId=helmut_lang&logNo=150043851844"
		htmlFileName = "naver.blog.1.html"
		extractedFileName = htmlFileName + ".extracted"
		downloadedFileName = htmlFileName + ".downloaded"

		# extract.py test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s extract.py '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(extractedFileName)
		self.assertEqual(expected, result)

		# download test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s download_image.pl '%s'" % (extractedFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(downloadedFileName)
		self.assertEqual(expected, result)


	def test_ollehmarket_webtoon(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "ollehmarket.webtoon.1.conf.xml"
		url = "http://comic.ollehmarket.com/webtoon/detail.nhn?titleId=548870&no=118"
		htmlFileName = "ollehmarket.webtoon.1.html"
		extractedFileName = htmlFileName + ".extracted"
		processedFileName = htmlFileName + ".processed"
		downloadedFileName = htmlFileName + ".downloaded"

		# extract.py test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s extract.py '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(extractedFileName)
		self.assertEqual(expected, result)

		# post process test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s %s/ollehmarket/post_process_ollehmarketwebtoon.pl '%s'" % (extractedFileName, os.environ['FEED_MAKER_CONF_FILE'], os.environ['FEED_MAKER_CWD'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(processedFileName)
		self.assertEqual(expected, result)

		# download test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s download_image.pl '%s'" % (processedFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(downloadedFileName)
		self.assertEqual(expected, result)


	def test_yonginlib(self):
		os.environ['FEED_MAKER_CONF_FILE'] = "yonginlib.2.conf.xml"
		url = "http://ebook.yonginlib.go.kr/Kyobo_T3/Content/ebook/ebook_View.asp?barcode=9788960605060&product_cd=001&category_id=1231"
		htmlFileName = "yonginlib.2.html"
		extractedFileName = htmlFileName + ".extracted"

		# extract.py test
		cmd = "cat %s | env FEED_MAKER_CONF_FILE=%s extract.py '%s'" % (htmlFileName, os.environ['FEED_MAKER_CONF_FILE'], url)
		result = feedmakerutil.exec_cmd(cmd)
		expected = feedmakerutil.read_file(extractedFileName)
		self.assertEqual(expected, result)


if __name__ == "__main__":
	unittest.main()
