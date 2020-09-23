#! /usr/bin/env python3

import argparse
import json
import os
from os.path import join as join_path
from subprocess import check_output, check_call, CalledProcessError
import re
from math import ceil
import pathlib
import logging

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

def capitalize_each_word(s, delimiter):
	return delimiter.join([w.capitalize() for w in s.split(delimiter)])

def transform_description(desc):
	new_desc = ""
	for i, line in enumerate(desc.split("\n")):
		line = "." if line == "" else line.strip()
		new_desc += line + "\n"
		if i != 0: line = " " + line
	return new_desc.strip()

def transform_maintainer(maint):
	return "{} <{}>".format(maint["name"], maint["email"])

def run_command(command, shell=True):
	return check_output(command, shell=shell).decode().strip()

def copy(src, dest, exclude=[], verbose=False):
	cmd = ["rsync", "-a", src, dest]
	if verbose: cmd[1] += "v"
	for e in exclude: cmd += ["--exclude", e]
	out = run_command(cmd, shell=False)
	if verbose: print(out)
	return out

def move(src, dest):
	return run_command(["mv", src, dest], shell=False)

def rm(src):
	return run_command(["rm", "-r", src], shell=False)

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("app_version", help="version to tag deb file with")
	parser.add_argument("app_location", default=os.getcwd(), nargs="?", type=os.path.abspath, help="location of app to package")
	parser.add_argument("--dest", default=os.getcwd(), type=os.path.abspath, help="where to output deb file")
	parser.add_argument("--log-level", default="INFO", choices=["CRITICAL", "50", "ERROR", "40", "WARNING", "30", "INFO", "20", "DEBUG", "10", "NOTSET", "0"], help="how verbose")
	args = parser.parse_args()

	if args.app_location.endswith(os.sep): args.app_location = args.app_location[:-1]
	os.environ["SRC"] = args.app_location
	logging.basicConfig(format="%(asctime)s %(message)s")
	LOGGER.setLevel(args.log_level)
	verbose = LOGGER.level > logging.INFO

	CONFIG_KEYS = {
		"package" : {
			"default" : os.environ["SRC"].split(os.sep)[-1],
			"validation" : None,
			"transform" : str.strip
		},
		"section" : {
			"default" : None,
			"validation" : lambda x: x in ["admin", "cli-mono", "comm", "database", "debug", "devel", "doc", "editors", "education", "electronics", "embedded", "fonts", "games", "gnome", "gnu-r", "gnustep", "graphics", "hamradio", "haskell", "httpd", "interpreters", "introspection", "java", "javascript", "kde", "kernel", "libdevel", "libs", "lisp", "localization", "mail", "math", "metapackages", "misc", "net", "news", "ocaml", "oldlibs", "otherosfs", "perl", "php", "python", "ruby", "rust", "science", "shells", "sound", "tasks", "tex", "text", "utils", "vcs", "video", "web", "x11", "xfce", "zope"],
			"transform" : str.strip
		},
		"priority" : {
			"default" : "optional",
			"validation" : lambda x: x in ["required", "important", "standard", "optional"],
			"transform" : str.strip
		},
		"architecture" : {
			"default" : run_command("dpkg --print-architecture"),
			"validation" : None,
			"transform" : str.strip
		},
		"depends" : {
			"default" : [],
			"validation" : None,
			"transform" : lambda x: [d.strip() for d in x]
		},
		"maintainer" : {
			"default" : "{} <{}>".format(run_command("git config user.name"), run_command("git config user.email")),
			"validation" : lambda x: bool(re.compile(".+ <.+@.+\..+>").match(x)),
			"transform" : transform_maintainer
		},
		"description" : {
			"default" : None,
			"validation" : None,
			"transform" : transform_description
		}
	}

	# Read config file
	with open(join_path(os.environ["SRC"], "debpack", "config.json"), "r") as f: config = json.loads(f.read().strip())
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
		if CONFIG_KEYS[k]["validation"] is not None and not CONFIG_KEYS[k]["validation"](config[k]): raise ValueError("{} failed validation (offending value: \"{}\")".format(k, config[k]))

	# Set remaining keys
	config["version"] = args.app_version if re.search("-[0-9]$", args.app_version) else args.app_version + "-1"

	# Ser extra vars
	build_script = join_path(os.environ["SRC"], "debpack", "build")
	architecture = config["architecture"]

	try:
		# Make structure
		LOGGER.debug("Making deb file structure")
		dirname = "{}_{}".format(config["package"], config["version"])
		original_files = os.listdir() + [dirname + "_" + architecture + ".deb"]

		# Work in tmp directory
		LOGGER.debug("Working in temp folder")
		destination = join_path(os.sep, "tmp", dirname)
		os.environ["DEST"] = join_path(destination, "data")
		pathlib.Path(destination, "control").mkdir(parents=True)
		pathlib.Path(destination, "data").mkdir(parents=True)
		os.chdir(destination)

		# Throw in maintainer scripts
		for script_name in SCRIPTS:
			script_file = join_path(os.environ["SRC"], "debpack", "maintainer_scripts", script_name)
			if os.path.isfile(script_file):
				LOGGER.debug("Adding {}".format(script_name))
				copy(script_file, "control", verbose=verbose)

		# Build
		if os.path.isfile(build_script):
			os.chdir("data")
			LOGGER.debug("Running build script")
			check_call([build_script])
			os.chdir("..")
		else:
			LOGGER.debug("No build script to execute")
		for src, dest in config["build"]["files"].items():
			if dest.startswith(os.sep): dest = dest[1:]
			dest = join_path("data", dest)
			dest_is_folder = dest.endswith(os.sep)
			folders = dest if dest_is_folder else os.sep.join(dest.split(os.sep)[:-1])
			run_command(["mkdir", "-p", folders], shell=False)
			copy(join_path(os.environ["SRC"], src), join_path(dest), exclude=["debpack", ".git", ".gitignore"], verbose=verbose)
		# Get another value that can't be determined until after build
		config["installed-size"] = ceil(int(run_command("du -s -B1 data | cut -f -1")) / 1024)

		# Write that one extra file
		with open("debian-binary", "w") as f: f.write("2.0\n")

		# Write control file
		s = ""
		for k in list(CONFIG_KEYS.keys()) + ["version", "installed-size"]:
			v = config[k]
			if isinstance(v, list):
				v = ", ".join(v)
			s += "{}: {}\n".format(capitalize_each_word(k, "-"), v)
		LOGGER.debug("Writing control file with contents:\n{}".format(s))
		with open(join_path("control", "control"), "w") as f: f.write(s)

		# Here, we will manually tar stuff because dpkg-deb does not use mutliple cores
		LOGGER.debug("Zipping control")
		run_command("tar --use-compress-program=pigz -cf control.tar.gz -C control .")
		LOGGER.debug("Zipping data")
		run_command("tar --use-compress-program=pigz -cf data.tar.gz -C data .")
		LOGGER.debug("Cleaning all but tarballs in build folder")
		rm("control")
		rm("data")
		run_command(["ar", "r", dirname + "_" + architecture + ".deb", "debian-binary", "control.tar.gz", "data.tar.gz"], shell=False)

		# Move to final destination
		move(dirname + "_" + architecture + ".deb", args.dest)

	finally:
		# Clean up
		LOGGER.debug("Cleaning up temp folder")
		try:
			pass
			rm(destination)
		except CalledProcessError:
			LOGGER.debug("Could not delete {}".format(dirname))
		os.chdir(args.app_location)
		LOGGER.debug("Working in source folder")
		LOGGER.debug("Cleaning up source folder")
		for f in [f for f in os.listdir() if f not in original_files]: rm(join_path(os.environ["SRC"], f))
