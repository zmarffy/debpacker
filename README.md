# debpack

debpack is a Debian package creation tool. It builds `deb` files from source code based off a configuration file and build script.

## Important features

* Easy integration into even enterprise-level build tools
* Super-simple JSON configuration file that can be easily generated

## Requirements

* `dpkg`, but, c'mon, you should already have that
* `python3`

## Setup

Install the deb package, which was, fun fact, created by `debpack` itself

## Code changes that need to be made

* Add an attempt to write to the destination location before proceeding to create the entire package just to realize permission denied
* Possibly add integration to `github-release`? Or at least explain how to do that
* Automatically pack README files and assign them to another command?
* Automatic setup of a local/real APT repository to drop packages into

## Debugging tips

* Run with `--log-level DEBUG`
