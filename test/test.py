#!/usr/bin/env python


import sys
import os
import filecmp
from bin.feed_maker_util import Process


def build_command(script, test_dir, index):
    """입력 fixture를 script에 파이프해 결과 임시 파일로 저장하는 셸 명령을 만든다."""
    return "cat %s/input.%d.txt | %s > %s/result.%d.temp" % (
        test_dir,
        index,
        script,
        test_dir,
        index,
    )


def test_script(script, work_dir, test_dir, index):
    os.chdir(work_dir)
    cmd = build_command(script, test_dir, index)
    # print(cmd)
    _, error = Process.exec_cmd(cmd)
    if not error:
        os.chdir(test_dir)
        return (
            filecmp.cmp("result.%d.temp" % (index), "expected.output.%d.txt" % (index)),
            "",
            cmd,
        )
    print(error)
    return False, error, cmd


def main() -> int:
    fm_cwd = os.getenv("FM_WORK_DIR")
    if not fm_cwd:
        print("can't get environment variable 'FM_WORK_DIR'")
        return -1

    test_subjects = {
        "naver/navercast": ["../capture_item_navercast.py"],
        "naver/naverblog.pjwwoo": ["../capture_item_naverblog.py"],
        "naver/castle2": ["../capture_item_naverwebtoon.py"],
        "naver/naverwebtoon": [
            "./capture_item_link_title.py",
            "./post_process_naverwebtoon.py 'http://comic.naver.com/webtoon/list?titleId=811707'",
        ],
        "naver/naverpost.interbiz": [
            "../capture_item_naverpost.py",
            "../post_process_naverpost.py",
        ],
        "kakao/kakaowebtoon": ["./capture_item_link_title.py"],
        "tistory/nasica1": ["../capture_item_tistory.py"],
        "funbe/lord_of_martial_library": [
            "../capture_item_funbe.py",
            "../post_process_funbe.py",
        ],
        "toonkor/perfect_surgeon": [
            "../capture_item_toonkor.py",
            "../post_process_toonkor.py",
        ],
        "wfwf/eldest_brother_of_martial_family": [
            "../capture_item_wfwf.py",
            "../remove_anchor_images.sh",
        ],
        "wtwt/a_returners_magic_should_be_special": ["../capture_item_wtwt.py"],
    }

    for feed, scripts in test_subjects.items():
        index = 0
        for script in scripts:
            index += 1
            print(feed)
            work_dir = fm_cwd + "/" + feed
            test_dir = fm_cwd + "/test/" + feed
            result, error, cmd = test_script(script, work_dir, test_dir, index)
            if not result or error:
                print("Error in %s of %s\n%s\n%s" % (feed, script, cmd, error))
                return -1
    print("Ok")
    return 0


if __name__ == "__main__":
    if os.environ.get("TEST", ""):
        import unittest

        class TestTestRunner(unittest.TestCase):
            def test_build_command_basic(self):
                self.assertEqual(
                    build_command("../capture_item_x.py", "/work/test/feed", 1),
                    "cat /work/test/feed/input.1.txt | ../capture_item_x.py "
                    "> /work/test/feed/result.1.temp",
                )

            def test_build_command_index_substituted(self):
                cmd = build_command("./s.py", "/t", 3)
                self.assertIn("input.3.txt", cmd)
                self.assertIn("result.3.temp", cmd)

            def test_build_command_includes_script_with_args(self):
                cmd = build_command("./post.py 'http://x'", "/t", 2)
                self.assertIn("| ./post.py 'http://x' >", cmd)

        sys.exit(unittest.main())
    else:
        sys.exit(main())
