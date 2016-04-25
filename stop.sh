#!/bin/bash

set -u

CWD=`pwd`
PROCESSES=`ps xa | grep $CWD/D20/__init__.py | grep -v grep`
if [[ $? -eq 1 ]]; then
	echo "Not running"
	exit
fi

set -e

PID=`echo $PROCESSES | awk '{print $1}'`
kill $@ $PID
