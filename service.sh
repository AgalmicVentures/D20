#!/bin/bash

set -u

##### Settings #####

COMMAND=D20/__init__.py

##### Helpers #####

CWD=`pwd`
PROCESS=$CWD/$COMMAND

function get_processes {
	ps xa | grep $PROCESS | grep -v grep
}

function start {
	PROCESSES=$(get_processes)
	if [[ $? -eq 0 ]]; then
		echo "Already running"
		return 0
	fi

	echo "Starting..."
	nohup $PROCESS &

	for N in 0 1 2 3 4 5 6 7 8 9; do
		PROCESSES=$(get_processes)
		if [[ $? -ne 0 ]]; then
			echo "Startup failed:"
			echo
			tail -n20 nohup.out
			return 1
		fi

		sleep 1
	done

	PROCESSES=$(get_processes)
	if [[ $? -eq 0 ]]; then
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

	for N in 0 1 2 3 4; do
		PID=`echo $PROCESSES | awk '{print $1}'`
		echo "Stopping PID $PID"
		kill $@ $PID
		sleep 1

		PROCESSES=$(get_processes)
		if [[ $? -eq 1 ]]; then
			echo "Stopped."
			return 0
		fi
		sleep 1
	done

	#If it's still alive, it's not responding to normal signals, so kill it
	echo "Killing PID $PID"
	kill -9 $PID
	sleep 1
}
