#!/usr/bin/env python3


import sys
import re
import feedmakerutil


def main():

    print('<meta name="viewport" content="width=device-width" />')
    print('<meta name="viewport" content="initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0" />')
    print('<style>* { max-width:100%; } a, pre { white-space: break-word; overflow-wrap: break-word; }</style>')

    for line in feedmakerutil.readStdinAsLineList():
        print(line)
                                        

if __name__ == "__main__":
    sys.exit(main())
