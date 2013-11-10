import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash, json

import base64
import re

DATABASE = '/home/cameron/app.db'
SECRET_KEY = "lolcoolasecretkey"
DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
	return sqlite3.connect(app.config['DATABASE'])

def is_empty_section(book, section):
	cur = g.db.execute("select * from comments where book=" + book + " AND section=" + section)
	entries = [cur.fetchall()]
	return len(entries[0]) == 0

def wordWrap(sentence):
	arr = sentence.split(" ")
	for i in range(len(arr)):
		arr[i] = "<span class='word'>" + arr[i] + "</span>"
	return " ".join(arr)

@app.template_filter()
def reverse(s):
	return s.replace("\\n", "<br/>")

@app.template_filter()
def by_sentence(s):
	#arr = s.split(".")
	arr = re.split(r'([.?!]+)', s)
	arr2 = list()
	for i in range(0, len(arr) - 1, 2):
		if is_empty_section(session["bookid"], str(i/2)):
			arr2.append("<span name='" + str(i/2) + "' class='nostyle'>" + wordWrap(arr[i]) + arr[i+1] + "</span>")
		else:
			arr2.append("<span name='" + str(i/2) + "' class='nostyle hasComments underline'>" + wordWrap(arr[i]) + arr[i+1] + "</span>")
	return ''.join(arr2)

@app.before_request
def before_request():
	g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
	db = getattr(g, 'db', None)
	if db is not None:
		db.close()

def getPass(user):
	cur = g.db.execute('select password from users WHERE name="' + user + '"')
	for row in cur.fetchall():
		return row[0]

def getID(user):
	cur = g.db.execute('select id from users WHERE name="' + user + '"')
	for row in cur.fetchall():
		return row[0]

def getUname(id):
	cur = g.db.execute('select name from users WHERE id = ' + str(id))
	for row in cur.fetchall():
		return row[0]

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['password'] != getPass(request.form['username']):
            error = 'Invalid password'
        else:
	    session['logged_in'] = True
            session['uid'] = getID(request.form['username'])
            flash('You were logged in')
            return redirect('/')
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
	g.db.execute("insert into users (name, password) VALUES(?, ?)", [request.form["username"], request.form["password"]])
	g.db.commit()
	return render_template("login.html")
    return render_template('register.html');

@app.route('/new_comment/<book>/<section>/<username>/<comment>', methods=["GET", "POST"])
def new_comment(book, section, username, comment):
	g.db.execute("insert into comments (section, book, username, comment) values (?, ?, ?, ?)", [section, book, username, base64.b64decode(comment)])
	g.db.commit()
	return "Success"

@app.route('/get_comments/<book>', methods=["GET", "POST"])
def get_comments(book):
	cur = g.db.execute("select comments.id, section, comment, users.name from comments INNER JOIN users ON comments.username=users.id where book = " + book)
	entries = [cur.fetchall()]
	return json.dumps(entries)

@app.route('/comments/<book>/<sentence>', methods=["GET", "POST"])
def comments(book, sentence):
	cur = g.db.execute("select comments.id, section, comment, users.name from comments INNER JOIN users ON comments.username=users.id where book = " + book + " and section=" + sentence)
	entries = [cur.fetchall()]
	return render_template("comments.html", book=book, section=sentence, uid=session["uid"], data=entries)

@app.route('/whoami')
def whoami():
	return "%d" % session['uid']

@app.route('/user/<user>')
def user_profile(user):
	#cur = g.db.execute('select bookid, books.title from finished INNER JOIN books ON finished.bookid=books.id where userid = '+str(session["uid"]))
	cur = g.db.execute('select bookid from finished where userid=' + user)
	books = [dict(id=row[0]) for row in cur.fetchall()]
	return render_template('user.html', uname=getUname(user), books=books)
	
@app.route('/read/<book>')
def read(book):
	g.db.execute('insert into finished(userid, bookid) values(' + str(session['uid']) + ', ' + book + ')')
	g.db.commit()
	return redirect("/")

@app.route('/add', methods=["GET", "POST"])
def add():
    if request.method == 'POST':
	    g.db.execute('insert into books(title, image, content) values("' + request.form['title'] + '", "' + request.form['cover'] + '", "' + request.form['content'] + '")')
	    g.db.commit()
            return redirect('/')
    return render_template("add.html")

@app.route('/logout')
def logout():
    session.pop('uid', "")
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect("/")

@app.route('/')
def index():
	if "uid" in session:
		cur = g.db.execute('select id, title, image from books')
		books = [dict(id=row[0], title=row[1], image=row[2]) for row in cur.fetchall()]
		return render_template('list.html', books=books)
	else:
		return render_template('landing.html')

@app.route('/users/')
def get_users():
	cur = g.db.execute('select id, name from users')
	users = [dict(id=row[0], name=row[1]) for row in cur.fetchall()]
	return render_template('users.html', users=users)

@app.route('/book/<id>')
def book(id):
	session["bookid"] = id
	cur = g.db.execute('select title, content from books where id = ' + id)
	cur2 = g.db.execute('select * from finished where bookid = ' + id + ' AND userid = ' + str(session["uid"]))
	book = [dict(title=row[0], content=row[1]) for row in cur.fetchall()]
	res = cur2.fetchall()
	return render_template('book.html', finished=len(res) >= 1, book=book[0], id=id)

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0')
