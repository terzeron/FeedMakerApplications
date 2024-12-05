#!/usr/bin/env python


import sys
import re
import getopt
from bin.feed_maker_util import IO


def main():
    num_of_recent_feeds = 1000
    optlist, _ = getopt.getopt(sys.argv[1:], "f:n:")
    for o, a in optlist:
        if o == '-n':
            num_of_recent_feeds = int(a)

    keyword_exclusion_list = ["가면라이더", "헥사기어", "Warhammer", "워해머", "아수라", "키즈나", "메가미", "카나메", "반간", "다간", "리베르 나이트", "창채소녀", "판타지 포레스트", "리벨 나이트", "루나마리아", "FRS", "젠레스", "니콜 데마라", "아니메스타", "30MS", "30ms", "츠키루나", "드라몬", "판타지스타", "30MF", "30mf", "베앗가이", "하츠네미쿠", "PLAMATEA", "유피아", "플라맥스", "미유키", "애니메스터", "제네 티어즈", "아르카나디아", "소피에라", "피겨라이즈", "미오리네", "램블랑", "블렛 엑소시스트", "시스루", "푸니모푸", "프레이아", "모데로이드", "프레임암즈", "하츠네 미쿠", "사이버 포뮬러", "사이버포뮬러", "SMP SRX", "말딸"]

    state = 0
    line_list = IO.read_stdin_as_line_list()
    result_list = []
    for line in line_list:
        if state == 0:
            m = re.search(r'<td class="subject">', line)
            if m:
                state = 1
        elif state == 1:
            #m = re.search(r'<a class="deco" href="(?P<link>[^\?"]+)[^"]*">\s*(?:<strong>)?\s*(?P<title>\S.+\S)\s*(?:</strong>)?\s*</a>', line)
            m = re.search(r'<a class="subject_link deco" href="(?P<link>[^\?"]+)[^"]*">', line)
            if m:
                link = m.group("link")
                link = re.sub(r'&amp;', '&', link)
                state = 2
        elif state == 2:
            m = re.search(r'^\s{3,}(?:<strong>)?\s*(?P<title>\S[^<>]+\S)\s*(?:</strong>)?\s{3,}', line)
            if m:
                title = m.group("title")
                state = 3
                for keyword in keyword_exclusion_list:
                    if keyword in title:
                        state = 0
                        break
                if state != 0:
                    result_list.append((link, title))
                    state = 0


    for (link, title) in result_list[:num_of_recent_feeds]:
        print("%s\t%s" % (link, title))


if __name__ == "__main__":
    sys.exit(main())
