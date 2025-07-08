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

while (ME:=os.environ.get('USER')) is None:
	import setup_admin
	setup_admin.makenv()


app = Flask(os.environ.get("appname",__name__))
app.config['KEY'] = os.environ.get('KEY', secrets.token_hex(32))


database = SqliteDatabase('instance/database.db')

class BaseModel(Model):
	class Meta: database = database
class Entries(BaseModel):
	id = AutoField(primary_key=True)
	title = CharField()
	content = TextField()
	date = IntegerField()
	class Meta: # pyrefly:ignore
		table_name = 'ENTRIES'
	@classmethod
	def byID(cls, id:Any, default:Any=None) -> Any:
		try: return cls.get_by_id(id)
		except DoesNotExist: return default


database.create_tables([Entries], safe=True)

def newEntry(title:str, content:str) -> Entries:
	return Entries(title=title, content=content, date=int(time.time())) #pyright: ignore

@app.before_request
def before():
	if RQ.path.startswith("/api"):
		auth = RQ.headers.get('Authorization', "").split(" ")
		if auth[0]!="Bearer": return jsonify({'error': 'Missing or invalid auth header'}), 400 #malformed
		if auth[1]!=os.environ.get('API_KEY',""): return jsonify({'error': 'Invalid API key'}), 401 #unauthorized

quote404 = [
	"I was never really here to begin with.",
	"I'm sorry, Dave. I'm afraid I can't do that.",
	"If something doesn't exist, create it yourself!",
	"It is pitch black. You are likely to be eaten by a grue.",
	"Keyboard not found, press any key to continue...",
	"Maybe you should just enjoy being lost for now"
	"The leather page is two IP blocks down.",
	"The page is in another castle",
	"The quote is a lie",
	"Turn it off and on again.",
	"Whatever it was it's not here.",
]
@app.errorhandler(404)
def page_not_found(e):
	return render_template('entry.html.jinja', d={"title":"What were you looking for???",
		"content":"<h1 class='big-404 cent'>404</h1><p class='cent'>page not found</p>"}, theme="normal",
		len=len, quote=random.choice(quote404)), 404











