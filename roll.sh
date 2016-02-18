#!/bin/bash

#Get the server pool
if [[ $# -gt 0 ]]
then
	echo "Seeding local entropy pool from $# servers"
	SERVERS=$@
else
	echo "Seeding local entropy pool from default server"
	SERVERS=https://agalmicventures.com:8443
fi

#Get the entropy from each server
for SERVER in $SERVERS
do
	echo "Getting entropy from $SERVER ..."

	#Calculate the hash of the highest resolution time available as a challenge (%N is nanos for GNU date)a
	START_TIME=`date +%Y%m%d%H%M%S%N`
	CHALLENGE=`echo $START_TIME | sha512sum | cut -d' ' -f1`
	EXPECTED_CHALLENGE_RESPONSE=`echo -n $CHALLENGE | sha512sum | cut -d' ' -f1`

	#Query the server and check the challenge response
	RESPONSE=`curl -s "$SERVER/api/entropy?challenge=$CHALLENGE"`
	CHALLENGE_RESPONSE=`echo $RESPONSE | egrep -o '(?"challengeResponse": ")[0-9a-f]+' | cut -d'"' -f4`
	if [ "$CHALLENGE_RESPONSE" = "$EXPECTED_CHALLENGE_RESPONSE" ]
	then
		#Pass through sha512sum to complicate writing a malicious server
		echo $RESPONSE | sha512sum > /dev/urandom
		echo "Success."
	else
		echo "Invalid challenge response (got $CHALLENGE_RESPONSE, expected $EXPECTED_CHALLENGE_RESPONSE)"
	fi
done

echo "Finished seeding local entropy pool."
