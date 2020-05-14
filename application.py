import os

from flask import Flask, render_template, request, session
from flask_session import Session
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
#DATABASE_URL = 'postgresql+psycopg2://qlesouarqdzvpk:667a3563007212e9a1d9b5b478fa439f17a5e0e32d2eff602855fd0d399b3fb3@ec2-18-209-187-54.compute-1.amazonaws.com:5432/d10dsm9g49lrku';
DATABASE_URL = 'sqlite:///books.db'


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(DATABASE_URL)
s = scoped_session(sessionmaker(bind=engine))
meta = MetaData()


@app.route("/", methods=["POST", "GET"])
def index():
    firstname = request.form.get("firstname")
    lastname = request.form.get("lastname")
    email = request.form.get("email")
    psw = request.form.get("psw")
    psw_repeat = request.form.get("psw-repeat")
    output_text = "Hello {} {}, your email address is {} and your password is {}".format(firstname, lastname, email, psw)
    return render_template("index.html", output_text=output_text)

@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
	app.run()