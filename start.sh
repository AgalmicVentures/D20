#!/bin/bash

set -u

PROCESSES=`ps xa | grep D20/__init__.py | grep -v grep`
if [[ $? -eq 0 ]]; then
	echo "Already running"
	exit
fi

set -e

echo "Starting..."
nohup ./D20/__init__.py &
sleep 1
echo "Started."
