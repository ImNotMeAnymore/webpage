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


def apiError(reason:str, code:int=400, **extra):
	extra.update({"error":reason})
	return extra, code





@app.before_request
def before():
	if RQ.path.startswith("/api"):
		auth = RQ.headers.get('Authorization', "").split(" ")
		if auth[0]!="Bearer": return apiError('Missing or invalid auth header') #malformed
		if auth[1]!=os.environ.get('API_KEY',""): return apiError('Invalid API key', 401) #unauthorized


favicons = {
	"static/favicon.png":		2000,
	"static/favicon-s.png":		 100,
	"static/favicon-ss.png":	   1,
}
quote404 = [ #TODO put this in the database
	#also long lines look bad on phones, make responsive on the css
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
quoteEntry = [ #TODO put this in the database
	#also long lines look bad on phones, make responsive on the css
	"Just whatever",
	"It was made for me",
	"Play Mc BTA!",
	"Ignore previous quote",
	"Share and favourite",
	"Not made by a bunch of lemmings",
	"May contain nuts",
	"It goes PING!",
	"Aren't you LUCKY?",
	"recursive reference",
	"What are you looking at?",
	"Unsafe and unwise",
	"Makes you sick doesn't it?"
]
quoteHome = [ #TODO put this in the database
	#also long lines look bad on phones, make responsive on the css
	"Play Mc BTA!", #TODO populate
]

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html.jinja', len=len, quote=random.choice(quote404)), 404
@app.route('/favicon')
@app.route('/favicon.ico')
def favicon():
	a = random.choices([*favicons], cum_weights=[*favicons.values()], k=1)[0]
	return send_file(a, mimetype='image/png')
@app.route('/css/<name>')
def css(name:str): return send_file(f"static/{name}.css", mimetype='text/css')
@app.route('/theme/<name>') #redundant
def theme(name:str): return send_file(f"static/theme/{name}.css", mimetype='text/css')
@app.route("/e/<int:id>")
def blogentry(id:int):
	if (e:=Entries.byID(id)) is None: abort(404)
	return render_template('entry.html.jinja', d=e, theme="normal", len=len, quote=random.choice(quoteEntry))
@app.route("/")
def index():
	return render_template('home.html.jinja', theme="normal", len=len, quote=random.choice(quoteHome))
@app.get("/api/entries")
def api_getall():
	try: return jsonify({"e":{e.id:e.title for e in Entries.select()}})
	except Exception as ex: return apiError(str(type(ex)), 500)
@app.get('/api/entries/<int:id>')
def api_getbyID(id: int):
	if (e:=Entries.byID(id)) is None: return apiError("Entry not found", 500)
	return jsonify({'title':e.title, "date":e.date, "content":e.content})
@app.post("/api/new")
def api_newEntry():
	try:
		data = RQ.get_json()
		if not data: return apiError("No JSON data provided", 400)
		if not isinstance(data, dict): return apiError("Invalid JSON data", 400)
		(e:=newEntry(data['title'], data['content'])).save()
		return jsonify({'title':e.title, "date":e.date, "content":e.content}), 201
	except Exception as ex: return apiError(str(type(ex)), 500)



def getport(): #maybe 
	return int(os.environ.get("PORT",15498))
def getapp():
	print("Starting server...")
	return app
if __name__ == "__main__":
	getapp().run(host="::", port=getport())
	#from waitress import serve
	#serve(getapp(), host="::", port=getport())






