import os

from flask import Flask, render_template, request, session, flash, redirect, url_for
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
s.current_user = None
meta = MetaData()
meta.reflect(bind=engine)
# Users = meta.tables['Users']
# Books = meta.tables['Books']
# Reviews = meta.tables['Reviews']


def search_exact(search_entry, col, table):
    sql_string = "SELECT * from {} where {} = '{}'".format(table,col,search_entry)
    result = s.execute(sql_string).fetchall()
    s.commit()
    if result:
        return result[0]
    else:
        return None
    
def search_approx(search_entry, col, table):
    sql_string = "SELECT * from {} where {} like '%{}%'".format(table,col,search_entry)
    result = s.execute(sql_string).fetchall()
    s.commit()
    if result:
        return result[0]
    else:
        return None

def login_credentials_check(email_addy, pwd):
    flag = False
    result = search_exact(email_addy, 'username', 'Users')
    if not result:
        return flag
    else:
        flag = result[2]== pwd
        return flag   




@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "GET":
        output_text = ""
        return render_template("index.html", output_text=output_text)
    else:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        psw = request.form.get("psw")
        psw_repeat = request.form.get("psw-repeat")

        result = search_exact(email, 'username', 'Users')

        if result is None:
            Users = meta.tables['Users']
            ins = Users.insert().values(username = email, password = psw, lastname = lastname, firstname = firstname)
            s.execute(ins)
            s.commit()
            output_text = "Hello {} {}! Thank you for registering.".format(firstname, lastname)
            return render_template("login.html", output_text=output_text)          
        else:
            flash('A user with that username/email already exists. Please retry or log in ', "danger")
            return redirect(url_for('index',_anchor='error_msg_anchor'))




@app.route('/login',methods=["POST", "GET"])
def login(output_text=""):
    if request.method == "GET":
        return render_template('login.html', output_text=output_text)
    else:
        email = request.form.get("email")
        psw = request.form.get("psw")
        flag = login_credentials_check(email, psw)
        if not flag:
            flash('Username or password incorrect. Please try again ', "danger")
            return redirect(url_for('login',_anchor='error_msg_anchor'))
        else: 
            s.current_user = email
            [_,userid, pwd, lname, fname] = list(search_exact(email, 'username','Users'))
            output_text = "You are logged in as {} {}.".format(fname, lname)
            return render_template('search_books.html', output_text=output_text)


@app.route('/logout',methods=["POST", "GET"])
def logout():
    s.current_user = None
    return render_template('login.html')

@app.route('/search_books',methods=["POST"])
def search_books():
    info = ""
    req = request.form
    isbn = req["isbn"]
    title = req["title"]
    lastname = req["lastname"]
    firstname = req["firstname"]
    info = "you searched for isbn: {}, title: {}, and Author {} {}". format(isbn, title, firstname, lastname)
    return render_template('search_books.html', info=info)



if __name__ == '__main__':
	app.run(debug = True)