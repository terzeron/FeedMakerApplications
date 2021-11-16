#!/usr/bin/env python


import sys
import os
import filecmp
from feed_maker_util import Process


def test_script(script, work_dir, test_dir, index):
    os.chdir(work_dir)
    cmd = "cat %s/input.%d.txt | %s > %s/result.%d.temp" % (test_dir, index, script, test_dir, index)
    #print(cmd)
    _, error = Process.exec_cmd(cmd)
    if not error:
        os.chdir(test_dir)
        return filecmp.cmp("result.%d.temp" % (index), "expected.output.%d.txt" % (index)), "", cmd
    print(error)
    return False, error, cmd


def main() -> int:
    fm_cwd = os.getenv("FEED_MAKER_WORK_DIR")
    if not fm_cwd:
        print("can't get environment variable 'FEED_MAKER_WORK_DIR'")
        return -1

    test_subjects = {
        "naver/navercast": [ "../capture_item_navercast.py" ],
        "naver/naverblog.pjwwoo": [ "../capture_item_naverblog.py" ],
        "naver/private_educational_institute_in_end_of_a_century": [ "../capture_item_naverwebtoon.py" ],
        "naver/naverwebtoon": [ "./capture_item_link_title.py" ],
        "naver/naverpost.businessinsight": [ "../capture_item_naverpost.py", "../post_process_naverpost.py" ],
        "kakao/kakaowebtoon": [ "./capture_item_link_title.py" ],
        "tistory/nasica1": [ "../capture_item_tistory.py" ],
        "egloos/oblivion": [ "../capture_item_link_title.py" ],
        "agit/gang_with_sword" : [ "../capture_item_agit.py" ],
        "buzztoon/devil_sword_king" : [ "../capture_item_buzztoon.py" ],
        "copytoon/extraordinary_god_of_martial_arts" : [ "../capture_item_copytoon.py" ],
        "jmana/one_punch_man_remake" : [ "../capture_item_jmana.py" ],
        #"manatoki/level_up_alone" : [ "../capture_item_manatoki.py" ],
        "marumaru/vegabond" : [ "../capture_item_marumaru.py" ],
        "ornson/weird_taoist_of_mudang" : [ "../capture_item_ornson.py" ],
        "wfwf/warrior_at_fff_level" : [ "../capture_item_wfwf.py" ],
        "wtwt/login_alone" : [ "../capture_item_wtwt.py" ],
    }

    for (feed, scripts) in test_subjects.items():
        index = 0
        for script in scripts:
            index += 1
            print(feed)
            work_dir = fm_cwd + "/" + feed
            test_dir = fm_cwd + "/test/" + feed
            _, error, cmd = test_script(script, work_dir, test_dir, index)
            if error:
                print("Error in %s of %s\n%s\n%s" % (feed, script, cmd, error))
                return -1
    print("Ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
