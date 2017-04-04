#!/usr/bin/env python


import sys


def main():
    if sys.argv[1].endswith(".pdf"):
        print("이 문서는 PDF이기 때문에 문서의 내용이 첨부되지 않았습니다.<br>")
        print("다음 링크를 직접 참고하시기 바랍니다.<br>")
        print("<a href='%s'>%s</a>" % (sys.argv[1], sys.argv[1]))
    else:
        for lines in sys.stdin:
            print(lines, end='')


if __name__ == "__main__":
    main()
