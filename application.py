import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "2Pge4GCffgiBlwSEyxdD8g", "isbns": "9781632168146"})
print(res.json())

app = Flask(__name__)

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

#Login route
@app.route('/login')
def login():
    return render_template('login.html')

#Register route
@app.route('/register')
def register():
    return render_template('register.html')


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
