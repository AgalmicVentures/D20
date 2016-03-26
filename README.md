# D20
D20 is an entropy microservice and client. As a network source of entropy, it is useful when there is little available otherwise. For example, newly cloned VM's would start with the same pool, and have limited user input.

The D20 server offers a service comparable to Pollen (https://github.com/dustinkirkland/pollen), but with several key differences. Superficially, D20 has a different algorithm to generate entropy and is written in Python rather than Go. However, the most important difference is the license: D20 has a far more permissive license than Pollen (MIT versus Affero GPL). This ensures you can modify and use it as you need, without worrying about licensing issues.

The D20 client (`roll.sh`) has similar differences with the Pollen client, Pollinate (https://github.com/dustinkirkland/pollinate). Again, the license is less restrictive (MIT versus GPL). Also, it does not send any unnecessary identifying information (such as OS and CPU) to the server.

For an open D20 server, go to https://www.agalmicventures.com:8443/api/entropy.

## FAQ

### Where do you get the entropy?
Random bytes read from `/dev/urandom`.

### Is `/dev/urandom` really secure? Don't you want to use `/dev/random`?
Yes. As long as you trust the crypto primitives you rely on the rest of the time. This is well covered here: http://www.2uo.de/myths-about-urandom/.

### How can I trust the server?
You don't have to. The client accepts a list of servers to use. As long as at least one instance is not compromised, your pool will get seeded securely.

Also, run your own server! The code is open source and short so you can verify it yourself.

### Challenge-response?
Although it can't prove the server gave you good entropy, it does prove that the server did some work and generated a unique response for your request. It also acts as a check that the client queried a valid D20 server.

### How does `roll.sh` generate its challenges?
It uses SHA512 sum of the date with nanosecond precision (`date +%Y%m%d%H%M%S%N`).

### How do I automate this?
You can reseed automatically once each day by adding the following to your crontab (`crontab -e`):

    #Set MM and HH to minute and hour of your choice.
    MM HH * * * cd path/to/D20/ && ./roll.sh

## API

### `/api/entropy`
Requires a single argument `challenge`. Returns a JSON blob containing 3 keys:

* `time`: the server time to the second (to prevent releasing fine-grained timing information) in ISO 8601 format (%Y-%m-%dT%H:%M:%S)
* `challengeResponse`: the SHA512 sum of the `challenge` as a lower case hexadecimal string
* `entropy`: the SHA512 sum of the challenge and 64 bytes drawn from `/dev/urandom` as a lower case hexadecimal string

## Scripts

### `start.sh`, `stop.sh`, `restart.sh`
These scripts will start, stop, and restart a background instance of D20 using `server.conf` as the configuration.

### `roll.sh`
Seeds your local entropy pool by individually seeding from a group of D20 instances specified as arguments: `./roll.sh https://d20.example.com`. If no arguments are specified, https://www.agalmicventures.com:8443 is used by default.
