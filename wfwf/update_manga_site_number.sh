#!/bin/bash

if [ "$1" == "" ]; then
    echo "must specify site number"
    exit 1
fi

exit 0

number=$1

perl -pi -e 's/^number=\d+/number='${number}'/g' check_*.sh
perl -pi -e 's/(newtoki|manamoa|wfwf)\d+/$1'${number}'/g' */conf.xml
rm -rf */newlist
