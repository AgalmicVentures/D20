# D20
D20 is an entropy microservice and client. As a network source of entropy, it is useful when there is little available otherwise. For example, newly cloned VM's would start with the same pool, and have limited user input.

The D20 server offers a service comparable to Pollen (https://github.com/dustinkirkland/pollen), but with several key differences. Superficially, D20 has a different algorithm to generate entropy and is written in Python rather than Go. However, the most important difference is the license: D20 has a far more permissive license than Pollen (MIT versus Affero GPL). This ensures you can modify and use it as you need, without worrying about licensing issues.

The D20 client (`roll.sh`) has similar differences with the Pollen client, Pollinate (https://github.com/dustinkirkland/pollinate). Again, the license is less restrictive (MIT versus GPL), to ensure, for example, that there will be no issues building a client into a product. Additionally, it does not send any unnecessary identifying information to the server, such as OS and CPU.

For an open D20 server, go to https://www.agalmicventures.com:8443/api/entropy.

## FAQ

### Where do you get the entropy?
Random bytes read from `/dev/urandom`.

### Is `/dev/urandom` really secure? Don't you want to use `/dev/random`?
Yes. As long as you trust the crypto primitives you rely on the rest of the time. This is well covered here: http://www.2uo.de/myths-about-urandom/.

### How can I trust this service?
You don't have to. Use it as one source of many, even other instances of D20 controlled by other parties. As long as at least one instance is not compromised, your pool will get seeded.

Also, run your own copy! It's open source and deliberately short so you can verify (and modify) the code yourself.

### Challenge-response?
Yes. To prove that the server did some work and generated a unique response for your request.

## API

### `/api/entropy`
Requires a single argument `challenge`. Returns a JSON blob containing 3 keys:

* `time`: the server time to the second (to prevent releasing fine-grained timing information)
* `challengeResponse`: the SHA512 sum of the `challenge`
* `entropy`: the SHA512 sum of the challenge and 64 bytes drawn from `/dev/urandom`

## Scripts

### `start.sh`, `stop.sh`, `restart.sh`
These scripts will start, stop, and restart a background instance of D20 using `server.conf` as the configuration.

### `roll.sh`
Seeds your local entropy pool by individually seeding from a group of D20 instances specified as arguments: `./roll.sh https://agalmicventures.com:8443`.
