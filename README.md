# debpack

`debpack` is a Debian package creation tool. It builds `deb` files from source code based off a configuration file and build script.

## Important features

* Easy integration into even enterprise-level build tools
* Super-simple JSON configuration file that can be easily generated

## Requirements

* `dpkg`, but, c'mon, you should already have that
* `python3`
* `pigz`

## Setup

Install the deb package, which was, fun fact, created by `debpack` itself

## Creating your first DEB file with debpacker

### Structure

When working on an application, a folder should be placed in the root of the source code called `debpack`. The structure of this folder is as shown.

```
source_code_folder/
└── debpack/
    ├── config.json
    ├── build
    └── maintainer_scripts/
        ├──preinst
        ├──new-preinst
        ├──old-preinst
        ├──postinst
        ├──old-postinst
        ├──conflictor's-postinst
        ├──deconfigured's-postinst
        ├──prerm
        ├──old-prerm
        ├──new-prerm
        ├──postrm
        ├──old-postrm
        ├──disappearer's-postrm
        └──new-postrm
```

#### The `config.json` file

The `config.json` file is the file that determines what metadata the Debian package will be tagged with and where source/compiled files should be placed.

#### The `build` script

This is the script that is run in order to compile or otherwise build the source code files in a certain manner. You should use it to do something with the source code files and place them into the target folder. This is provided for convenience as the evironment variable `SRC`.

Why do I use this? Because I never learned `make`! Yay, reinventing the wheel!

#### The `maintainer-scripts`

These are the `apt` control scripts that run under certain conditions. See [here](https://www.debian.org/doc/manuals/maint-guide/dreq.en.html) for more info.

## Code changes that need to be made

* Add an attempt to write to the destination location before proceeding to create the entire package just to realize permission denied
* Possibly add integration to `github-release`? Or at least explain how to do that
* Automatically pack README files and assign them to another command?
* Automatic setup of a local/real APT repository to drop packages into
* Add changelog support

## Debugging tips

* Run with `--log-level DEBUG`
