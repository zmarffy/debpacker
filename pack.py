#! /usr/bin/env python3

import argparse
import json
import os
from os.path import join as join_path
from subprocess import check_output, check_call
import re
import shutil

SCRIPTS = [
	"preinst",
	"new-preinst",
	"old-preinst",
	"postinst",
	"old-postinst",
	"conflictor's-postinst",
	"deconfigured's-postinst"
	"prerm",
	"old-prerm",
	"new-prerm",
	"postrm",
	"old-postrm",
	"disappearer's-postrm",
	"new-postrm"
]

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

parser = argparse.ArgumentParser()
parser.add_argument("app_version", help="version to tag deb file with")
parser.add_argument("app_location", default=os.getcwd(), nargs="?", help="location of app to package")
args = parser.parse_args()

os.environ["APP_LOCATION"] = args.app_location

CONFIG_KEYS = {
	"package" : {
		"default" : os.environ["APP_LOCATION"].split(os.sep)[-1],
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
		"validation" : lambda x: bool(re.compile("(.+) <.+@.+>").match(x)),
		"transform" : transform_maintainer
	},
	"description" : {
		"default" : None,
		"validation" : None,
		"transform" : transform_description
	}
}

# Read config file
with open(join_path(os.environ["APP_LOCATION"], "debpack", "config.json"), "r") as f: config = json.loads(f.read().strip())

# Work in tmp directory
os.chdir(os.sep + "tmp")

# Set defaults, transform, and validate
for k, v in CONFIG_KEYS.items():
	if k not in config.keys():
		v = CONFIG_KEYS[k]["default"]
		if v is not None:
			print("WARNING: Using default for {} ({})".format(k, v))
			config[k] = v
		else:
			raise ValueError("{} cannot be empty".format(k))
	config[k] = CONFIG_KEYS[k]["transform"](config[k])
	if CONFIG_KEYS[k]["validation"] is not None and not CONFIG_KEYS[k]["validation"](config[k]): raise ValueError("{} failed validation (offending value: \"{}\")".format(k, v))
# Set remaining keys
config["version"] = args.app_version

# Make structue
dirname = "{}_{}".format(config["package"], config["version"])
os.environ["DEST"] = join_path(os.sep, "tmp", dirname)
os.mkdir(dirname)
os.mkdir(join_path(dirname, "DEBIAN"))

# Write control file
s = ""
for k, v in config.items():
	if isinstance(v, list):
		v = ", ".join(v)
	s += "{}: {}\n".format(k.capitalize(), v)
with open(join_path(dirname, "DEBIAN", "control"), "w") as f: f.write(s)

# Throw in extra scripts
for script_name in SCRIPTS:
	script_file = join_path(os.environ["APP_LOCATION"], "debpack", script_name)
	if os.path.isfile(script_file): shutil.copy2(script_file, join_path(os.environ["DEST"], "DEBIAN"))

# Build
check_call([join_path(os.environ["APP_LOCATION"], "debpack", "build")])
run_command(["dpkg-deb", "--build", dirname], shell=False)
shutil.rmtree(dirname)