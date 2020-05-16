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
meta = MetaData()
meta.reflect(bind=engine)
Users = meta.tables['Users']
Books = meta.tables['Books']
Reviews = meta.tables['Reviews']


def tabelize(u):
    return [list(row) for row in u]


# exact search function
def search_exact(search_entry, col, table):
    '''returns database row as a list'''
    sql_string = "SELECT * from {} where {} = '{}'".format(table,col,search_entry)
    result = s.execute(sql_string).fetchall()
    s.commit()
    if not result:
        return None
    else:
        result = tabelize(result)
        return result[0]
    
def search_approx(search_entry, col, table):
    '''returns database rows as a lists of lists'''
    sql_string = "SELECT * from {} where {} like '%{}%'".format(table,col,search_entry)
    result = s.execute(sql_string).fetchall()
    s.commit()
    if result:
        return tabelize(result)
    else:
        return None
    
    
def login_credentials_check(email_addy, pwd):
    flag = False
    result = search_exact(email_addy, 'username', 'Users')
    s.commit()
    if not result:
        return flag
    else:
        flag = result[2]== pwd
        return flag   

def search_book_database(isbn, title, author, year):
    sql_string = "SELECT * from 'Books' where 1==1"
    if isbn != "":
        sql_string += " and isbn like '%{}%'".format(isbn)
    if title != "":
        sql_string += " and title like '%{}%'".format(title)
    if author != "":
        sql_string += " and author like '%{}%'".format(author)
    if year != "":
        sql_string += " and year == {}".format(year)

    results = tabelize(s.execute(sql_string))
    s.commit()
    return results


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
            session["current_user"] = email
            [_,_, _, lname, fname] = search_exact(session["current_user"], 'username','Users')
            who_dis_text = "You are logged in as {} {}.".format(fname, lname)
            info = ""
            results = []
            return render_template('search_books.html', info=info, results = results, who_dis_text=who_dis_text)


@app.route('/logout',methods=["POST"])
def logout():
    session["current_user"] = None
    return render_template('login.html')

@app.route('/search_books',methods=["POST"])
def search_books():
    info = ""
    results = []
    [_,_, _, lname, fname] = search_exact(session["current_user"], 'username','Users')
    who_dis_text = "You are logged in as {} {}.".format(fname, lname)
    req = request.form
    isbn = req["isbn"]
    title = req["title"]
    author = req["author"]
    year = req["year"]
    if all([x=='' for x in (isbn, title, author, year)]):
        info = "Please fill in at least one of the fields above."
        return render_template('search_books.html', info=info, results = results, who_dis_text=who_dis_text)
    else:
        results = search_book_database(isbn, title, author, year)
        info = "{} books found for this search". format(len(results))
        return render_template('search_books.html', info=info, results = results, who_dis_text=who_dis_text)
    



if __name__ == '__main__':
	app.run(debug = True)