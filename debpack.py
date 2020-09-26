#! /usr/bin/env python3

import argparse
import json
import os
from os.path import join as join_path
from os.path import expanduser
from subprocess import check_output, check_call, CalledProcessError, PIPE
import re
import datetime
import pytz
from tzlocal import get_localzone
from math import ceil
import pathlib
import logging
import sys

pathlib.Path(expanduser("~"), ".debpacker").mkdir(exist_ok=True)

LOGGER = logging.getLogger()

SCRIPTS = [
    "preinst",
    "new-preinst",
    "old-preinst",
    "postinst",
    "old-postinst",
    "conflictor's-postinst",
    "deconfigured's-postinst",
    "prerm",
    "old-prerm",
    "new-prerm",
    "postrm",
    "old-postrm",
    "disappearer's-postrm",
    "new-postrm"
]


os.environ["SRC"] = os.getcwd()
PACKAGE_NAME = os.environ["SRC"].split(os.sep)[-1]


def capitalize_each_word(s, delimiter):
    return delimiter.join([w.capitalize() for w in s.split(delimiter)])


def _transform_description(desc):
    new_desc = ""
    for i, line in enumerate(desc.split("\n")):
        line = "." if line == "" else line.strip()
        new_desc += line + "\n"
        if i != 0:
            line = " " + line
    return new_desc.strip()


def _transform_maintainer(maint):
    return "{} <{}>".format(maint["name"], maint["email"])


def run_command(command, shell=True):
    try:
        return check_output(command, stderr=PIPE, shell=shell).decode().strip()
    except CalledProcessError as e:
        LOGGER.critical(e.stderr.decode().strip())
        raise e


def copy(src, dest, exclude=[], verbose=False):
    cmd = ["rsync", "-a", src, dest]
    if verbose:
        cmd[1] += "v"
    for e in exclude:
        cmd += ["--exclude", e]
    out = run_command(cmd, shell=False)
    if verbose:
        print(out)
    return out


def move(src, dest):
    return run_command(["mv", src, dest], shell=False)


def rm(src):
    return run_command(["rm", "-r", src], shell=False)


def get_commit_messages(last_commit_id_to_include=None):
    remove_one_commit = last_commit_id_to_include is None
    use_all_commits = False
    commit_id_found = False
    if last_commit_id_to_include is None:
        try:
            with open(join_path(expanduser("~"), ".debpacker", PACKAGE_NAME, ".lci"), "r") as f:
                last_commit_id_to_include = f.read().strip()
        except FileNotFoundError:
            use_all_commits = True

    out = run_command(["git", "-C", os.environ["SRC"], "--no-pager", "log",
                       "--reflog", "--no-color", "--pretty=format:%H,%s"], shell=False)
    commits = []
    for commit in out.split("\n"):
        data = commit.split(",", 1)
        commits.append(data)
        if not use_all_commits and last_commit_id_to_include is not None and data[0].startswith(last_commit_id_to_include):
            commit_id_found = True
            break
    if not use_all_commits and remove_one_commit:
        commits = commits[0:-1]
    if last_commit_id_to_include is not None and not commit_id_found:
        raise ValueError("Could not find commit {}".format(
            last_commit_id_to_include))
    return commits


def _format_changes_string(o):
    if isinstance(o, str):
        return "\n".join(["* {}".format(c) for c in o.split("\n")])
    elif isinstance(o, list):
        return "\n".join(["* {} ({})".format(m[0], m[1]) for m in o])
    else:
        raise ValueError("Trying to format an unsupported type")


def _get_changes_from_input():
    changes_string = sys.stdin.read()
    changes_string = changes_string.strip()
    if not changes_string.endswith("\n") or not changes_string:
        print()
    if not changes_string:
        LOGGER.debug("No changes provided")
        changes_string = "Repack of last version"
    return changes_string


def get_last_commit_id_and_generate_changes_string(last_commit_id_to_include=None):
    last_commit_id = None
    commit_messages = get_commit_messages(
        last_commit_id_to_include=last_commit_id_to_include)
    if len(commit_messages) == 0:
        print("No new git commits; please enter a changelog:")
        changes_string = _format_changes_string(_get_changes_from_input())
    else:
        last_commit_id = commit_messages[0][0]
        changes_string = _format_changes_string(commit_messages)
    return last_commit_id, changes_string


def _parse_changelog(s):
    if s is None or s == "":
        return None, None
    elif s == "auto":
        return "auto", None
    else:
        option, message = "message", s # Default
        for o in ["message", "from_commit_id"]:
            if s.startswith(o + "="):
                option = o
                message = s.split("=", 1)[1]
                break
        return option, message


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("app_version", help="version to tag deb file with")
    parser.add_argument("-a", "--architecture_all", action="store_true",
                        help="if package is not architecture-specifc")
    parser.add_argument("--dest", default=os.getcwd(),
                        type=os.path.abspath, help="where to output deb file")
    parser.add_argument("--log_level", default="INFO", choices=[
                        "CRITICAL", "50", "ERROR", "40", "WARNING", "30", "INFO", "20", "DEBUG", "10", "NOTSET", "0"], help="how verbose")
    parser.add_argument("-c", "--gen_changelog", default=None,
                        type=_parse_changelog, nargs="?", const=("message", None), help="generate a changelog") # Need to doc more
    parser.add_argument("--urgency", default="medium", type=str.lower, choices=[
                        "low", "medium", "high", "emergency", "critical"], help="urgency of this update")

    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s %(message)s")
    LOGGER.setLevel(args.log_level)
    verbose = LOGGER.level > logging.INFO

    CONFIG_KEYS = {
        "section": {
            "default": None,
            "validation": lambda x: x in ["admin", "cli-mono", "comm", "database", "debug", "devel", "doc", "editors", "education", "electronics", "embedded", "fonts", "games", "gnome", "gnu-r", "gnustep", "graphics", "hamradio", "haskell", "httpd", "interpreters", "introspection", "java", "javascript", "kde", "kernel", "libdevel", "libs", "lisp", "localization", "mail", "math", "metapackages", "misc", "net", "news", "ocaml", "oldlibs", "otherosfs", "perl", "php", "python", "ruby", "rust", "science", "shells", "sound", "tasks", "tex", "text", "utils", "vcs", "video", "web", "x11", "xfce", "zope"],
            "transform": str.strip
        },
        "priority": {
            "default": "optional",
            "validation": lambda x: x in ["required", "important", "standard", "optional"],
            "transform": str.strip
        },
        "depends": {
            "default": [],
            "validation": None,
            "transform": lambda x: [d.strip() for d in x]
        },
        "maintainer": {
            "default": "{} <{}>".format(run_command("git config user.name"), run_command("git config user.email")),
            "validation": lambda x: bool(re.compile(".+ <.+@.+\..+>").match(x)),
            "transform": _transform_maintainer
        },
        "description": {
            "default": None,
            "validation": None,
            "transform": _transform_description
        }
    }

    # Read config file
    try:
        with open(join_path(os.environ["SRC"], ".debpack", "config.json"), "r") as f:
            config = json.loads(f.read().strip())
    except FileNotFoundError:
        raise FileNotFoundError(
            "No debpack configuration file found; are you in the right source folder?") from None
    LOGGER.debug("Config loaded")

    # Set defaults, transform, and validate
    for k, v in CONFIG_KEYS.items():
        if k not in config.keys():
            v = CONFIG_KEYS[k]["default"]
            if v is not None:
                LOGGER.warning("Using default for {} ({})".format(k, v))
                config[k] = v
            else:
                raise ValueError("{} cannot be empty".format(k))
        config[k] = CONFIG_KEYS[k]["transform"](config[k])
        if CONFIG_KEYS[k]["validation"] is not None and not CONFIG_KEYS[k]["validation"](config[k]):
            raise ValueError(
                "{} failed validation (offending value: \"{}\")".format(k, config[k]))

    # Set remaining keys
    config["version"] = args.app_version if re.search(
        "-[0-9]$", args.app_version) else args.app_version + "-1"
    if not args.architecture_all:
        config["architecture"] = run_command("dpkg --print-architecture")
        LOGGER.debug("Using architecture {}".format(config["architecture"]))
    else:
        config["architecture"] = "all"
    config["package"] = PACKAGE_NAME

    # Create folder for writing persistent data
    pathlib.Path(expanduser("~"), ".debpacker",
                 PACKAGE_NAME).mkdir(exist_ok=True)

    # Ser extra vars
    build_script = join_path(os.environ["SRC"], ".debpack", "build")
    architecture = config["architecture"]
    last_commit_id = None

    try:
        LOGGER.debug("Making deb file structure")
        dirname = "{}_{}".format(PACKAGE_NAME, config["version"])
        original_files = os.listdir() + [dirname + "_" + architecture + ".deb"]

        # Work in tmp directory
        LOGGER.debug("Working in temp folder")
        destination = join_path(os.sep, "tmp", dirname)
        os.environ["DEST"] = join_path(destination, "data")

        # Make structure
        pathlib.Path(destination, "control").mkdir(parents=True)
        pathlib.Path(destination, "data").mkdir(parents=True)
        os.chdir(destination)

        # Throw in maintainer scripts
        for script_name in SCRIPTS:
            script_file = join_path(
                os.environ["SRC"], ".debpack", "maintainer_scripts", script_name)
            if os.path.isfile(script_file):
                LOGGER.debug("Adding {}".format(script_name))
                copy(script_file, "control", verbose=verbose)

        # Add changelog
        if args.gen_changelog != (None, None):
            if args.gen_changelog[0] == "from_commit_id":
                last_commit_id = args.gen_changelog[1]
                last_commit_id, changes_string = get_last_commit_id_and_generate_changes_string(
                    last_commit_id_to_include=last_commit_id)
            elif args.gen_changelog[0] == "auto":
                last_commit_id, changes_string = get_last_commit_id_and_generate_changes_string()
            elif args.gen_changelog[0] == "message":
                changes_string = args.gen_changelog[1]
                if changes_string is None:
                    print("Please enter a changelog:")
                    changes_string = _get_changes_from_input()
                changes_string = _format_changes_string(changes_string)
            else:
                raise parser.error("Invalid option for gen_changelog")

            LOGGER.debug("Constructing and writing changelog")
            pathlib.Path("data", "usr", "share", "doc",
                         PACKAGE_NAME).mkdir(parents=True)
            changelog_title_string = "{} ({}) any; urgency={}".format(
                PACKAGE_NAME, config["version"], args.urgency)
            changelog_changes_string = "\n".join(
                ["  " + l for l in changes_string.split("\n")])
            changelog_author_string = " -- {}  {}".format(config["maintainer"], datetime.datetime.strftime(
                pytz.timezone(get_localzone().zone).localize(datetime.datetime.now()), "%a, %d %b %Y %X %z"))
            changelog_string = "\n\n".join(
                [changelog_title_string, changelog_changes_string, changelog_author_string])
            LOGGER.info("Changes:\n{}".format(changes_string))
            # This is likely tiny so there is no reason to gzip it
            with open(join_path("data", "usr", "share", "doc", PACKAGE_NAME, "changelog.Debian"), "w") as f:
                f.write(changelog_string)

        # Build/compile/whatever your code
        if os.path.isfile(build_script):
            os.chdir("data")
            LOGGER.debug("Running build script")
            check_call([build_script])
            os.chdir("..")
        else:
            LOGGER.debug("No build script to execute")
        for src, dest in config["build"]["files"].items():
            if dest.startswith(os.sep):
                dest = dest[1:]
            dest = join_path("data", dest)
            dest_is_folder = dest.endswith(os.sep)
            folders = dest if dest_is_folder else os.sep.join(
                dest.split(os.sep)[:-1])
            run_command(["mkdir", "-p", folders], shell=False)
            copy(join_path(os.environ["SRC"], src), join_path(dest), exclude=[
                 ".debpack", ".git", ".gitignore"], verbose=verbose)
        # Get another value that can't be determined until after build
        config["installed-size"] = ceil(
            int(run_command("du -s -B1 data | cut -f -1")) / 1024)

        # Write that one extra file
        with open("debian-binary", "w") as f:
            f.write("2.0\n")

        # Write control file
        s = ""
        for k in list(CONFIG_KEYS.keys()) + ["package", "version", "installed-size", "architecture"]:
            v = config[k]
            if isinstance(v, list):
                v = ", ".join(v)
            s += "{}: {}\n".format(capitalize_each_word(k, "-"), v)
        LOGGER.debug("Writing control file with contents:\n{}".format(s))
        with open(join_path("control", "control"), "w") as f:
            f.write(s)

        # Here, we will manually tar stuff because dpkg-deb does not use mutliple cores
        LOGGER.debug("Zipping control")
        run_command(
            "tar --use-compress-program=pigz -cf control.tar.gz -C control .")
        LOGGER.debug("Zipping data")
        run_command("tar --use-compress-program=pigz -cf data.tar.gz -C data .")
        LOGGER.debug("Cleaning all but tarballs in build folder")
        rm("control")
        rm("data")
        run_command(["ar", "r", dirname + "_" + architecture + ".deb",
                     "debian-binary", "control.tar.gz", "data.tar.gz"], shell=False)

        # Move to final destination
        move(dirname + "_" + architecture + ".deb", args.dest)

        if last_commit_id is not None:
            with open(join_path(expanduser("~"), ".debpacker", PACKAGE_NAME, ".lci"), "w") as f:
                f.write(last_commit_id)

    finally:
        # Clean up
        LOGGER.debug("Cleaning up temp folder")
        try:
            rm(destination)
        except CalledProcessError:
            LOGGER.debug("Could not delete {}".format(dirname))
        os.chdir(os.environ["SRC"])
        LOGGER.debug("Working in source folder")
        LOGGER.debug("Cleaning up source folder")
        for f in [f for f in os.listdir() if f not in original_files]:
            rm(join_path(os.environ["SRC"], f))
