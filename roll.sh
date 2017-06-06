#!/bin/bash

# Copyright (c) 2015-2017 Agalmic Ventures LLC (www.agalmicventures.com)
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

set -u

readonly START_WAIT_MAX=15
readonly STEP_WAIT_MAX=2

#Get the server pool
if [[ $# -gt 0 ]]
then
	echo "Seeding local entropy pool from $# servers"
	SERVERS="$*"
else
	echo "Seeding local entropy pool from default server"
	SERVERS=https://agalmicventures.com:8443
fi

echo "Waiting to start (randomized to prevent server contention)..."
python3 -c "import random, time; time.sleep($START_WAIT_MAX * random.random())"

#Alias sha512sum if necessary on OS X
SHA512=$(which sha512sum)
if [[ $? -gt 0 ]] ; then
	echo "Aliasing sha512sum to shasum..."
	SHA512="shasum -a 512"
fi

#Get the entropy from each server
for SERVER in $SERVERS
do
	echo "Getting entropy from $SERVER ..."

	#Calculate the hash of the highest resolution time available as a challenge (%N is nanos for GNU date)a
	START_TIME=$(date +%Y%m%d%H%M%S%N)
	CHALLENGE=$(echo "$START_TIME" | $SHA512 | cut -d' ' -f1)
	EXPECTED_CHALLENGE_RESPONSE=$(echo -n "$CHALLENGE" | $SHA512 | cut -d' ' -f1)

	#Query the server and check the challenge response
	RESPONSE=$(curl -s "$SERVER/api/entropy?challenge=$CHALLENGE")
	CHALLENGE_RESPONSE=$(echo "$RESPONSE" | grep -Eo '"challengeResponse": "[0-9a-f]+' | cut -d'"' -f4)
	if [ "$CHALLENGE_RESPONSE" = "$EXPECTED_CHALLENGE_RESPONSE" ]
	then
		#Pass through sha512sum to complicate writing a malicious server
		echo "$RESPONSE" | $SHA512 > /dev/urandom
		echo "Success."
	else
		echo "Invalid challenge response (got $CHALLENGE_RESPONSE, expected $EXPECTED_CHALLENGE_RESPONSE)"
	fi

	#Random wait in between
	python3 -c "import random, time; time.sleep($STEP_WAIT_MAX * random.random())"
done

echo "Finished seeding local entropy pool."
