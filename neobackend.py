#!/usr/bin/python3.13
#!waitress-serve --port=15498 --call backend:start #

import os
import random
import re
import hashlib
from typing import (Any)
from flask import (
	Flask,
	request as RQ,
	abort,
	send_file,
	render_template,
	#send_from_directory,
	redirect,
	#url_for,
	session,
	jsonify
)
from peewee import (
	SqliteDatabase,
	AutoField,
	CharField,
	TextField,
	IntegerField,
	Model,
	DoesNotExist
)
#import sqlite3
import time
import secrets


def loadenv():
	with open('.env', 'r') as f: #just raise if it doesn't exist
		for i in f.read().split("\n"):
			if i[0] == "#": continue
			if "=" in i:
				k,v = i.split('=', 1)
				os.environ[k] = v
try: loadenv()
except FileNotFoundError: pass #for now

app = Flask(os.environ.get("appname",__name__))




