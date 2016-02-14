# D20
D20 is an entropy microservice in Python 3 built on CherryPy. As a network source of entropy, it is useful when there is little entropy available otherwise. For example, newly cloned VM's with no user input would start with the same entropy pool.

It offers entropy-as-a-service, comparable to Pollen (https://github.com/dustinkirkland/pollen), but with several key differences. Superficially, D20 has a different algorithm to generate entropy and is written in Python rather than Go. However, the most important difference is the license: D20 has a far more permissive license than Pollen (MIT versus Affero GPL). This ensures you can modify and use it as you need, without worrying about licensing issues.

For an open instance, go to https://www.agalmicventures.com:8443/json/entropy.

## FAQ

### Where do you get the entropy?
Random bytes read from `/dev/urandom`.

### Is `/dev/urandom` really secure? Don't you want to use `/dev/random`?
Yes. As long as you trust the crypto primitives you rely on the rest of the time. This is well covered here: http://www.2uo.de/myths-about-urandom/

### How can I trust this service?
You don't have. Use it as one source of many, even other instances of D20 controlled by other parties. As long as at least one instance is not compromised, your pool will get seeded.

Also, run your own copy! It's open source and deliberately short so you can verify (and modify) the code yourself.

### Challenge-response?
Yes. To prove that the server did some work and generated a unique response for your request.

## API

### `/api/entropy`
Requires a single argument `challenge`. Returns a JSON blob containing 3 keys:

* `time`: the server time to the second (to prevent releasing fine-grained timing information)
* `challengeResponse`: the SHA512 sum of the `challenge`
* `entropy`: the SHA512 sum of the challenge and 64 bytes drawn from `/dev/urandom`
