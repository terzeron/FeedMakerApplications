#!/bin/bash

if [ "$1" == "" ]; then
    echo "must specify site number"
    exit 1
fi

export number=$1

perl -pi -e 's/^number=\d+/number=$ENV{"number"}/g' check_*.sh
perl -pi -e 's/\<list_url\>\<\!\[CDATA\[https:\/\/(newtoki|manamoa|wfwf)\d+/\<list_url\>\<\!\[CDATA\[https:\/\/$1$ENV{"number"}/g' */conf.xml
rm -rf */newlist
