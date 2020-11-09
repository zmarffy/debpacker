# `debpacker`

`debpacker` is a Debian package creation tool. It builds DEB files from source code based off a configuration file and build script.

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

### Structure

When working on an application, a folder should be placed in the root of the source code called `.debpack`. The structure of this folder is as shown.

```text
source_code_folder/
└── .debpack/
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

The `config.json` file is the file that determines what metadata the Debian package will be tagged with and where source/compiled files should be placed.

The `build` script is the script that is run in order to compile or otherwise build the source code files in a certain manner. You should use it to do something with the source code files and place them into the target folder. This is provided for convenience as the evironment variable `SRC`. Why do I use this? Because I never learned `make`! Yay, reinventing the wheel!

The `maintainer-scripts` are the `apt` control scripts that run under certain conditions. See [here](https://www.debian.org/doc/manuals/maint-guide/dreq.en.html) for more info. They will not be discussed in this documentaion, as this is not something specific to `debpacker` itself.

### Packing

Switch to the root directory of the source code and run `debpack [app version]`. It's as simple as that. Run `debpack --help` for more options.

### Creating your first DEB file with debpacker

Creating a DEB package with this tool is as simple as creating a configuration file with where the files are to be installed, creating a build script, and running a command when read to pack.

Here are two examples, one that requires compilation of code (C++) and one that does not (Python).

#### C++ example

Here's how the project's code is structured.

```text
helloworld-in-c++/
├── helloworld.cpp
└── .debpack/
    ├── config.json
    └── build
```

The `config.json` file is as follows.

```json
{
    "section" : "utils",
    "priority" : "optional",
    "maintainer" : {
        "name" : "Zeke Marffy",
        "email" : "zmarffy@yahoo.com"
    },
    "depends" : [
    ],
    "description" : "hello world in C++",
    "build" : {
        "files" : {
            "helloworld-c++" : "/usr/bin/helloworld-c++"
        }
    }
}
```

This file will specify to `debpacker` that this program is optional, the maintainer is Zeke Marffy, it does not require anything special to run, and when installed, the file `helloworld-c++` file will be placed in `/usr/bin/`. But wait, where does that file come from? It's not in the file structure of the project, right?

Let's talk about the build script.

The `build` script is as follows.

```shell
g++ helloworld.cpp -o helloworld-c++
```

This script will compile the code into a binary called `helloworld-c++`. Thus, `debpacker` will use that file.

There are no maintainer scripts needed for this program. Nothing is needed to be run before or after it is installed.

So then let's pack it!

Run `debpack 1.0` in the `helloworld-in-c++/` folder.

And now we have a hello world C++ program packaged up in a DEB file. It is only usabale on a machine of the same architecture of the machine that compiled it, remember!

#### Python example

Here's how the project's code is structured.

```text
helloworld-in-python/
├── helloworld.py
└── .debpack/
    └── config.json
```

Don't forget to make sure `helloworld.py` is executable.

The `config.json` file is as follows.

```json
{
    "section" : "utils",
    "priority" : "optional",
    "maintainer" : {
        "name" : "Zeke Marffy",
        "email" : "zmarffy@yahoo.com"
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

This file will specify to `debpacker` that this program is optional, the maintainer is Zeke Marffy, it requires Python 3 to run, and when installed, the `helloworld.py` script will be placed in `/usr/bin/`, renamed without "`.py`" at the end of it, for easy running. This JSON file also specifies that this package is usable on any architecture (`architecture_all`), due to the fact that Python is an interpreted language.

What about the `build` script? There is none? Correct! In the case of this "hello world" script, as touched on in the `config.json` explanation, there is no build script to execute, as Python is an interpreted language. This is totally OK; a `build` script is optional. `debpack` can just copy files directly into a DEB if you would like with no compilation or otherwise build steps.

There are no maintainer scripts needed for this program. Nothing is needed to be run before or after it is installed.

Let's pack this one next!

Run `debpack 1.0` in the `helloworld-in-python/` folder.

And now you have a hello world Python program packaged up in a DEB file.

### Extra features

* Generate a changelog for the DEB file with the `-c` option
* Automatically post resulting DEBs to GitHub's releases page with the `--github_release` option

### Notes

Some thoughts to consider when it comes to packing an entirely Python program.

* Should you *really* be using `debpacker` to do that, or could you do it with a `pip` package?
* Is it a good idea to list Python dependencies as `apt` dependencies? A lot of system-package-manager-managed Python packages are not up to date, and certainly tons and tons are not even available via any known repos. Maybe you should put the installation of these in a maintainer script.
* How are you going to perform imports of Python files that are off in different locations? I do have an answer to this one, actually. You can use [`zmtools`](https://github.com/zmarffy/zmtools)'s `get_module` function, which will allow you to specify where the Python module you want to import is.

Please, if you are unsure of how to use this tool, open an issue or (even better) email me. I am happy to assist you in fitting it into your project. So long as I don't get a lot of people asking me. :P
