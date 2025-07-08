#!/usr/bin/python3.13
#!waitress-serve --port=15498 --call backend:start #

import os
import random
import re
import hashlib
from typing import (
	Any
)
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
# from flask_sqlalchemy import SQLAlchemy
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

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

database = SqliteDatabase('instance/database.db')

ME = os.environ.get('USER')
PWH = os.environ.get('PASS_HASH',"")

# Peewee models
class BaseModel(Model):
	class Meta: database = database

class Entries(BaseModel):
	id = AutoField(primary_key=True)
	title = CharField(unique=True)
	content = TextField()
	date = IntegerField()

	class Meta: # pyrefly:ignore
		table_name = 'ENTRIES'
	
	@classmethod
	def byID(cls, id:Any, default:Any=None) -> Any:
		try: return cls.get_by_id(id)
		except DoesNotExist: return default



# with app.app_context(): db.create_all()

database.create_tables([Entries], safe=True)

def isForbidden(ip:str) -> bool:
	return False #for now

def sanitize_html(content):
	"""Remove script tags and event handlers from HTML content"""
	# Remove script tags and their content
	content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
	
	# Remove event handlers (onclick, onload, etc.)
	# Match on* attributes with double quotes
	content = re.sub(r'\s*on\w+\s*=\s*"[^"]*"', '', content, flags=re.IGNORECASE)
	# Match on* attributes with single quotes
	content = re.sub(r"\s*on\w+\s*=\s*'[^']*'", '', content, flags=re.IGNORECASE)
	# Match on* attributes with unquoted values
	content = re.sub(r'\s*on\w+\s*=\s*[^>\s]+', '', content, flags=re.IGNORECASE)
	
	# Remove javascript: URLs
	content = re.sub(r'javascript:[^\s"\'<>]*', '', content, flags=re.IGNORECASE)
	
	return content

def newEntry(title, content) -> Entries:
	return Entries(title=title, content=sanitize_html(content), date=int(time.time())) #pyright: ignore

# Simple API Authentication
###def require_api_auth(f):
###	"""Decorator to require simple API key authentication"""
###	def wrapper(*args, **kwargs):
###		auth_header = RQ.headers.get('Authorization')
###		if not auth_header or not auth_header.startswith('Bearer '):
###			return jsonify({'error': 'Missing or invalid authorization header'}), 401
###		
###		token = auth_header.split(' ')[1]
###		api_key = os.environ.get('API_KEY')
###		if not api_key or token != api_key:
###			return jsonify({'error': 'Invalid API key'}), 401
###		
###		return f(*args, **kwargs)
###	wrapper.__name__ = f.__name__
###	return wrapper

def validate_entry_data(data):
	"""Validate entry data for API operations"""
	if not isinstance(data, dict):
		return False, "Invalid JSON data"
	
	if 'title' not in data or not data['title'].strip():
		return False, "Title is required"
	
	if 'content' not in data or not data['content'].strip():
		return False, "Content is required"
	
	if len(data['title']) > 200:
		return False, "Title must be 200 characters or less"
	
	return True, None

@app.before_request
def before():
	e = RQ.environ
	ip = e.get('HTTP_X_FORWARDED_FOR')or e['REMOTE_ADDR']
	if isForbidden(ip):
		return redirect("https://"+".".join(str(random.randint(0,255))for i in range(4)))#or some other nonsense
	if RQ.path.startswith("/admin"):
		print(ip,"requested", RQ.path)
		if not session.get("auth"): return jsonify({'error': 'Not logged in'}), 401
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


@app.route("/")
def index():
	return "test"


@app.post("/login")
def login_p():
	session['auth'] = RQ.form.get('username',"")==ME and\
		hashlib.sha256(RQ.form.get('password',"").encode()).hexdigest()==PWH
	return redirect("/admin")
@app.get("/login")
def login_g(): return render_template('login.html.jinja')


@app.route("/logout")
def logout():
	session.pop('auth')
	return redirect("/")

@app.route("/admin")
def admin():
	return render_template('admin.html.jinja', entries=Entries.select())


@app.post("/admin/new")
def writeEntry_p(): #handle the publishing entry stuff
	#assert on the webpage that the stuff is not, yknow, empty
	entry = newEntry(RQ.form.get("title", "UNTITLED"), RQ.form.get("content","[nothing]"))
	entry.save()
	return redirect("/admin")
@app.get("/admin/new")
def writeEntry_g():
	return render_template('edit_entry.html.jinja', entry=None)


@app.post("/admin/edit/<int:id>")
def editEntry_p(id:int):
	if (e:=Entries.byID(id)) is None: return abort(404) #this is stupid, pyrefly seems to be even worse than pyright
	e.title = RQ.form.get('title')
	e.content = sanitize_html(RQ.form.get('content'))
	e.save()
	return redirect("/admin")
@app.get("/admin/edit/<int:id>")
def editEntry_g(id:int):
	if (e:=Entries.byID(id)) is None: return abort(404)
	return render_template('edit_entry.html.jinja', entry=e)
@app.get("/admin/delete/<int:id>")
def delete_entry_confirm(id:int):
	if (e:=Entries.byID(id)) is None: return abort(404)
	return render_template('delete_confirm.html.jinja', entry=e)
@app.post("/admin/delete/<int:id>")
def delete_entry(id:int):
	if (e:=Entries.byID(id)) is not None: e.delete_instance()
	return redirect("/admin")
@app.route("/e/<int:id>")
def blogentry(id:int):
	if (e:=Entries.byID(id)) is None: return abort(404)
	return render_template('entry.html.jinja', d=e, theme="normal", len=len)

@app.route('/theme/<name>')
def theme(name:str): return send_file(f"static/theme/{name}.css", mimetype='text/css')
@app.route('/css/<name>')
def css(name:str): return send_file(f"static/{name}.css", mimetype='text/css')

favicons = {
	"static/favicon.png":		2000,
	"static/favicon-s.png":		 100,
	"static/favicon-ss.png":	   1,
}
@app.route('/favicon')
@app.route('/favicon.ico')
def favicon():
	a = random.choices([*favicons], cum_weights=[*favicons.values()], k=1)[0]
	return send_file(a, mimetype='image/png')



port = 15498

# API Endpoints

@app.get("/api/entries")
def api_get_entries():
	try: return jsonify({"e":{e.id:e.title for e in Entries.select()}})
	except Exception as ex: return jsonify({'error': str(type(ex))}), 500

###@app.route('/api/entries', methods=['GET'])
###@require_api_auth
###def api_get_entries():
###	"""Get all entries"""
###	try:
###		entries = []
###		for entry in Entries.select():
###			entries.append({
###				'id': entry.id,
###				'title': entry.title,
###				'content': entry.content,
###				'date': entry.date
###			})
###		return jsonify({'entries': entries})
###	except Exception as e:
###		return jsonify({'error': str(e)}), 500
@app.route('/api/entries/<int:id>', methods=['GET'])
def api_get_entry(id: int):
	"""Get a specific entry"""
	try:
		entry = Entries.byID(id)
		if not entry:
			return jsonify({'error': 'Entry not found'}), 404
		
		return jsonify({
			'id': entry.id,
			'title': entry.title,
			'content': entry.content,
			'date': entry.date
		})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

@app.route('/api/entries', methods=['POST'])
def api_create_entry():
	"""Create a new entry"""
	try:
		data = RQ.get_json()
		if not data:
			return jsonify({'error': 'No JSON data provided'}), 400
		
		is_valid, error = validate_entry_data(data)
		if not is_valid:
			return jsonify({'error': error}), 400
		
		# Check if title already exists
		existing = Entries.select().where(Entries.title == data['title']).exists()
		if existing:
			return jsonify({'error': 'Entry with this title already exists'}), 409
		
		entry = newEntry(data['title'], data['content'])
		entry.save()
		
		return jsonify({
			'id': entry.id,
			'title': entry.title,
			'content': entry.content,
			'date': entry.date
		}), 201
	except Exception as e:
		return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<int:id>', methods=['PUT'])
def api_update_entry(id: int):
	"""Update an existing entry"""
	try:
		data = RQ.get_json()
		if not data:
			return jsonify({'error': 'No JSON data provided'}), 400
		
		is_valid, error = validate_entry_data(data)
		if not is_valid:
			return jsonify({'error': error}), 400
		
		entry = Entries.byID(id)
		if not entry:
			return jsonify({'error': 'Entry not found'}), 404
		
		# Check if title already exists (excluding current entry)
		existing = Entries.select().where(
			(Entries.title == data['title']) & (Entries.id != id)
		).exists()
		if existing:
			return jsonify({'error': 'Entry with this title already exists'}), 409
		
		entry.title = data['title']
		entry.content = sanitize_html(data['content'])
		entry.save()
		
		return jsonify({
			'id': entry.id,
			'title': entry.title,
			'content': entry.content,
			'date': entry.date
		})
	except Exception as e:
		return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<int:id>', methods=['DELETE'])
# yeah these are all ai trash in case you didn't realize
def api_delete_entry(id: int):
	"""Delete an entry"""
	try:
		entry = Entries.byID(id)
		if not entry:
			return jsonify({'error': 'Entry not found'}), 404
		
		entry.delete_instance()
		return jsonify({'message': 'Entry deleted successfully'})
	except Exception as e:
		return jsonify({'error': str(e)}), 500



def getapp():
	print("Starting server...")
	return app
if __name__ == "__main__":
	#getapp().run(host="::", port=port)
	from waitress import serve
	serve(getapp(), host="::", port=port)
