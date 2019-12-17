import os

from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests


app = Flask(__name__)
app.secret_key = 'DODGE'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


#Register route
@app.route('/register', methods = ['POST', 'GET'])
def register():
    if request.method == 'POST':
        #Check for password
        if request.form['password'] == request.form['password2']:
            username = request.form['username']
            password = request.form['password']

            #check if user already register
            check_user = db.execute('SELECT username FROM users WHERE username = :username', {'username': username}).rowcount
            if check_user == 0:
                db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {'username': username, 'password': password})
                db.commit()

                #Register success
                flash(f'{username} is successfully register')
                return redirect(url_for('login'))
            else:
                flash('This user is already exist')
        else:
            #password doesn't match
            flash("Password does not match")
            return render_template('register.html')

    #return register page in get request
    return render_template('register.html')

#Login route
@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "POST":
        #check if username is valid
        username = request.form['username']
        password = request.form['password']
        check_user = db.execute('SELECT * From users WHERE username = :username', {'username': username}).fetchone()
        if check_user == None:
            flash('This username does not exist')
            return render_template('login.html')

        #Check Password
        if check_user['password'] == password:
            flash(f'HI {username}')
            session['username'] = username
            session['user_id'] = db.execute('SELECT user_id From users WHERE username = :username', {'username': username}).fetchone()[0]
            return redirect(url_for('index'))
        else:
            flash('Password does not match')
            return render_template('login.html')

    #GET request
    return render_template('login.html')

#LOGOUT
@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('login'))

#index route
@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == 'POST':
        keyword = request.form.get("search", None)
        if keyword is not None or keyword != '':
            result = db.execute("SELECT * FROM books WHERE title LIKE :title OR isbn LIKE :isbn OR author LIKE :author", {'title': f'%{keyword}%', 'isbn': f'%{keyword}%', 'author': f'%{keyword}%'}).fetchall()
            return render_template('result.html', keywords=result)

    return render_template('index.html')


#Book Page
@app.route("/result/<string:book_isbn>", methods=["POST", "GET"])
def book_page(book_isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn ", {'isbn': book_isbn}).fetchone()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "2Pge4GCffgiBlwSEyxdD8g", "isbns": book.isbn})
    res = res.json()['books'][0]
    comments = db.execute("SELECT * FROM comments, users WHERE book_id = :book_id AND users.user_id = comments.user_id", {'book_id': book.book_id}).fetchall()

    #Post a comment
    if request.method == 'POST':
        comment = request.form.get('comment')
        rate = request.form.get('rate')
        if comment is not None and comment != '':
            db.execute("INSERT INTO comments (text, user_id, book_id, rate) VALUES (:text, :user_id, :book_id, :rate)", {'text': comment, 'user_id': session['user_id'], 'book_id': book.book_id, 'rate': int(rate)})
            db.commit()
        return redirect(url_for('book_page', book_isbn = book.isbn))
    #Check if user make a comment on this book
    if request.method == 'GET':
        comment = None
        rate = None
        try:
            check_comment = db.execute("SELECT * FROM comments WHERE user_id = :user_id AND book_id = :book_id", {'user_id': session['user_id'], 'book_id': book.book_id}).fetchone()
            if check_comment:
                comment = check_comment.text
                rate = check_comment.rate
        except:
            pass
        return render_template('book_page.html', book_isbn = book.isbn, res = res, book = book, comment = comment, all_comments = comments, rate = rate)

@app.route("/api/<string:isbn>")
def api(isbn):
    try:
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn ", {'isbn': isbn}).fetchone()
        book_info = {}
        book_info['title'] = book.title
        book_info['author'] = book.author
        book_info['year'] = book.year
        book_info['isbn'] = book.isbn
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "2Pge4GCffgiBlwSEyxdD8g", "isbns": isbn})
        res = res.json()['books'][0]
        book_info['review_count'] = res['work_ratings_count']
        book_info['average_score'] = res['average_rating']
        return jsonify(book_info)
    except:
        abort(404)

if __name__ =='__main__':
    app.run(debug=True)
