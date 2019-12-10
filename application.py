import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
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

#index route
@app.route("/")
def index():
    return render_template('index.html')

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
        check_user = db.execute('SELECT username FROM users WHERE username = :username', {'username': username}).rowcount
        if check_user == 0:
            flash('This username does not exist')
            return render_template('login.html')

        #Check Password
        check_pass = db.execute('SELECT * From users WHERE username = :username', {'username': username}).fetchone()
        if check_pass['password'] == password:
            flash(f'HI {username}')
            session['username'] = username
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
    return redirect(url_for('login'))

#Search result route
@app.route("/result", methods=["POST"])
def result():
    if request.method == 'POST':
        keyword = request.form.get("search", None)
        if keyword == None or keyword == '':
            return redirect(url_for('index'))

        #Search in database

        return render_template('result.html', keywords=keyword)


if __name__ =='__main__':
    app.run(debug=True)
