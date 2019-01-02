#!/bin/bash

# Copyright (c) 2015-2019 Agalmic Ventures LLC (www.agalmicventures.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#XXX: Disabled so the virtual environment will work (yes, this is ridiculous)
#set -u

##### Settings #####

readonly COMMAND=D20/Server.py

##### Helpers #####

readonly CWD=$(pwd)
readonly PROCESS="$CWD/$COMMAND"

function get_processes {
	# shellcheck disable=SC2009
	ps xa | grep "$PROCESS" | grep -v grep
}

function start {
	if get_processes > /dev/null; then
		echo "Already running"
		return 0
	fi

	#Automatically source a virtual environment if available
	if [ -e env/ ]; then
		# shellcheck disable=SC1091
		source env/bin/activate
	fi

	echo "Starting..."
	nohup "$PROCESS" "$@" &

	#Wait 10 seconds to ensure a successful start
	for _ in 0 1 2 3 4 5 6 7 8 9; do
		if get_processes > /dev/null; then
			sleep 1
		else
			break
		fi
	done

	if get_processes > /dev/null; then
		echo "Started."
		return 0
	else
		echo "Startup failed:"
		echo
		tail -n20 nohup.out
		return 1
	fi
}

function stop {
	PROCESSES=$(get_processes)
	if [[ $? -eq 1 ]]; then
		echo "Not running"
		return 0
	fi

	for _ in 0 1 2 3 4; do
		PIDS=$(echo "$PROCESSES" | awk '{print $1}')
		echo "Stopping PID $PIDS"
		kill "$@" "$PIDS"
		sleep 1

		PROCESSES=$(get_processes)
		if [[ $? -eq 1 ]]; then
			echo "Stopped."
			return 0
		fi
		sleep 1
	done

	#If it's still alive, it's not responding to normal signals, so kill it
	PIDS=$(echo "$PROCESSES" | awk '{print $1}')
	echo "Killing PID $PIDS"
	kill -9 "$PIDS"
	sleep 1
}
