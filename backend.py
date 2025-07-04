#!/usr/bin/python3.13
#!waitress-serve --port=15498 --call backend:start #

import random
from random import randint as rdi
from flask import Flask, g, request as RQ, abort, send_file, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import sqlite3


app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

class Entries(db.Model):
	__tablename__ = "ENTRIES"
	id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	title = db.Column(db.String, nullable=False, unique=True)
	content = db.Column(db.Text, nullable=False)
	date = db.Column(db.Integer, nullable=False)


#class NonoIP(db.Model):
#	__tablename__ = 'NONOIPS'
#	ip = db.Column(db.String, primary_key=True)
#class YesIP(db.Model):
#	__tablename__ = 'YESIPS'
#	ip = db.Column(db.String, primary_key=True)
with app.app_context(): db.create_all()






def isForbidden(ip:str) -> bool:
	return False #for now

	#return session.query(NonoIP).filter_by(ip=ip).first() is not None
	# blacklist

	#return db.session.query(YesIP).filter_by(ip=ip).first() is None
	# whitelist

	#ipv4 could be stored as a sinlge 8digit number ff.ff.ff.ff
	#sum((int(i)<<(24-n*8)) for n,i in enumerate(ip.split(".")))
	#192.168.1.1 -> 0xc0a80101

@app.before_request
def before():
	e = RQ.environ
	ip = e.get('HTTP_X_FORWARDED_FOR')or e['REMOTE_ADDR']
	if isForbidden(ip): abort(500) #or some other nonsense
	print(ip,"requested")



@app.errorhandler(404)
def page_not_found(e):
	data = {
		"title":"What were you looking for???",
		"content":"<h1 class='big-404 cent'>404</h1><p class='cent'>page not found</p>"
	}
	return render_template('entry.html.jinja', d=data, theme="normal",
		len=len, quote="Whatever it was it's not here."), 404










@app.route("/")
def index():
	return "test"


@app.route("/e/<int:id>")
def blogentry(id:int):
	data = db.session.get(Entries, id)
	if not data: abort(404)
	return render_template('entry.html.jinja', d=data, theme="normal", len=len)



@app.route('/theme/<name>')
def theme(name:str): return send_file(f"static/theme/{name}.css", mimetype='text/css')

@app.route('/css/<name>')
def css(name:str): return send_file(f"static/{name}.css", mimetype='text/css')

@app.route('/favicon')
def favicon():
	return send_file(f'static/favicon{"-s"if not rdi(0,5) else ""}.png', mimetype='image/png')






port = 15498
def getapp():
	print("Starting server...")
	return app
if __name__ == "__main__":
	#getapp().run(host="::", port=port)
	from waitress import serve
	serve(getapp(), host="::", port=port)
