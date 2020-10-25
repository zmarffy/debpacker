# `debpacker`

`debpacker` is a Debian package creation tool. It builds `deb` files from source code based off a configuration file and build script.

## Important features

* Easy integration into even enterprise-level build tools
* Super-simple JSON configuration file that can be easily generated

## Requirements

* `dpkg`, but, c'mon, you should already have that
* `python3`
* `pigz`
* `pytz` (a `pip` package)
* `tzlocal` (a `pip` package)
* `zmtools` (a `pip` package)
* `gh` (the GitHub CLI)

## Creating your first DEB file with debpacker

Creating a DEB package with this tool is as simple as creating a configuration file with where the files are to be installed, creating a build script, and running a command when read to pack.

### Structure

When working on an application, a folder should be placed in the root of the source code called `.debpack`. The structure of this folder is as shown.

```text
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

The `config.json` file is the file that determines what metadata the Debian package will be tagged with and where source/compiled files should be placed. Here is an example `config.json` file with an explanation of how `debpacker` will handle it.

```json
{
    "section" : "utils",
    "priority" : "optional",
    "maintainer" : {
        "name" : "Zeke Marffy",
        "email" : "zmarffy@me.com"
    },
    "depends" : [
        "python3",
    ],
    "description" : "hello world in Python",
    "build" : {
        "files" : {
            "helloworld.py" : "/usr/bin/helloworld-python"
        }
    },
    "architecture_all" : true
}
```

This file will specify to `debpacker` that this program is optional, the maintainer is Zeke Marffy, it requires Python 3 to run, and when installed, the `helloworld.py` script will be placed in `/usr/bin/`, remaned without `.py` at the end of it, for easy running. This JSON file also specifies that this package is usable on any architecture, due to the fact that Python is an interpreted langauge.

#### The `build` script

This is the script that is run in order to compile or otherwise build the source code files in a certain manner. You should use it to do something with the source code files and place them into the target folder. This is provided for convenience as the evironment variable `SRC`.

Why do I use this? Because I never learned `make`! Yay, reinventing the wheel!

In the case of a "hello world" script, as touched on in the `config.json` explanation, there is no build script to execute, as Python is an interpreted langauge. This is totally OK; a `build` script is optional. `debpack` can just copy files directly into a DEB if you would like with no compilation or otherwise build steps.

#### The `maintainer-scripts`

These are the `apt` control scripts that run under certain conditions. See [here](https://www.debian.org/doc/manuals/maint-guide/dreq.en.html) for more info.

### Packing

Switch to the root directory of the source code and run `debpack [app version]`. It's as simple as that. Run `debpack --help` for more options.

## Code changes that need to be made

* Add an attempt to write to the destination location before proceeding to create the entire package just to realize permission denied
* Automatically pack README files and assign them to another command?
* Automatic setup of a local/real APT repository to drop packages into
* bumpversion integraton
