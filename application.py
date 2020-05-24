import os, json, requests

from flask import Flask, render_template, request, session, flash, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
DATABASE_URL = 'postgres://qlesouarqdzvpk:667a3563007212e9a1d9b5b478fa439f17a5e0e32d2eff602855fd0d399b3fb3@ec2-18-209-187-54.compute-1.amazonaws.com:5432/d10dsm9g49lrku'
#DATABASE_URL = 'sqlite:///books.db'
API_KEY = 'XGCq2OkNCVFbu0qMbYaZg'


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
def remove_apostrophy(a):
    a = a.replace("\'", "\'\'")
    return a


# exact search function
def search_exact(search_entry, col, table):
    result =[]
    search_entry = remove_apostrophy(search_entry)
    sql_string = 'SELECT * from "{}" where "{}" like \'%{}%\' '.format(table,col,search_entry)
    try:
        result = s.execute(sql_string).fetchall()
    except:
        print("SQL querry failed")
        
    s.commit()
    if not result:
        return None
    else:
        result = tabelize(result)
        return result[0]
    
def search_approx(search_entry, col, table):
    result =[]
    search_entry = remove_apostrophy(search_entry)
    sql_string = 'SELECT * from "{}" where "{}" ilike \'%{}%\' '.format(table,col,search_entry)
    try:
        result = s.execute(sql_string).fetchall()
    except:
        print("SQL querry failed")
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
    title = remove_apostrophy(title)
    author = remove_apostrophy(author)
    sql_string = 'SELECT * from "Books" where 1=1'
    if isbn != "":
        sql_string += ' and "isbn" like \'%{}%\' '.format(isbn)
    if title != "":
        sql_string += ' and "title" ilike \'%{}%\' '.format(title)
    if author != "":
        sql_string += ' and "author" ilike \'%{}%\' '.format(author)
    if year != "":
        sql_string += ' and "year" = {}'.format(year)

    results = tabelize(s.execute(sql_string))
    s.commit()
    return results

def did_they_review_this(reviewer, book_isbn):
    result=False
    sql_command = 'SELECT * from "Reviews" where "username" = \'{}\' and isbn = \'{}\' '.format(reviewer,book_isbn)
    result = s.execute(sql_command).fetchall()
    s.commit()
    return bool(result)  
    

def get_book_data(isbn):
    new_dict = {}
    try:
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "XGCq2OkNCVFbu0qMbYaZg", "isbns": isbn})
        res_dict = res.json()['books'][0]
        [_,_,title,author,year] = search_exact(isbn, 'isbn', 'Books')
    except:
        return new_dict
    new_dict['isbn']=isbn
    new_dict['title']=title
    new_dict['author']=author
    new_dict['year']=year
    new_dict['review_count']=res_dict['work_ratings_count']
    new_dict['average_score']=res_dict['average_rating']
    return new_dict



def get_reviews(book_isbn):
    sql_command = 'SELECT * from "Reviews" where "isbn" = \'{}\' '.format(book_isbn)
    result = s.execute(sql_command).fetchall()
    s.commit()
    return result

@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("index.html")



@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        output_text = ""
        return render_template("register.html", output_text=output_text)
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
            return redirect(url_for('register',_anchor='error_msg_anchor'))




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


@app.route('/logout')
def logout():
    session["current_user"] = ""
    session["current_results"] = []
    return render_template('index.html')

@app.route('/search_books',methods=["POST"])
def search_books():
    info = ""
    results = []
    reviewed_or_not = []
    [_,_, _, lname, fname] = search_exact(session["current_user"], 'username','Users')
    who_dis_text = "You are logged in as {} {}.".format(fname, lname)
    req = request.form
    isbn = req["isbn"]
    title = req["title"]
    author = req["author"]
    year = req["year"]
    if all([x=='' for x in (isbn, title, author, year)]):
        info = "Please fill in at least one of the fields above."
        return render_template('search_books.html', info=info, results = results, reviewed_or_not = reviewed_or_not, who_dis_text=who_dis_text)
    else:
        results = search_book_database(isbn, title, author, year)
        reviewed_or_not=[int(did_they_review_this(session["current_user"], row[1])) for row in results]
        session["current_results"] = results
        info = "{} books found for this search". format(len(results))
        return render_template('search_books.html', info=info, results = results, reviewed_or_not = reviewed_or_not, who_dis_text=who_dis_text)

@app.route('/back_to_search', methods=["GET"])
def back_to_search():
    [_,_, _, lname, fname] = search_exact(session["current_user"], 'username','Users')
    who_dis_text = "You are logged in as {} {}.".format(fname, lname)
    results = session["current_results"] 
    reviewed_or_not=[int(did_they_review_this(session["current_user"], row[1])) for row in results]
    info = "{} books found for this search". format(len(results))
    return render_template('search_books.html', info=info, results = results, reviewed_or_not = reviewed_or_not, who_dis_text=who_dis_text)


    
@app.route('/api/<isbn>',methods=["GET"])
def api(isbn):
    info_dict = get_book_data(isbn)
    if info_dict:
        json_object = json.dumps(info_dict)
        return render_template('api.html', isbn=isbn, json_object=json_object)
    else:
        return render_template('page_not_found.html', isbn=isbn)

@app.route('/test',methods=["GET"])
def test():
    person = "Sourish"
    number = 0
    return render_template('test.html', person=person, number=number)

@app.route('/bookpage/<isbn>',methods=["GET", "POST"])
def bookpage(isbn):

    rating = ""
    review = ""
    submitted = "no"
    info_dict = get_book_data(isbn)
    if not info_dict:
        return render_template('page_not_found.html', isbn=isbn)
    else:
        [_,_, _, lname, fname] = search_exact(session["current_user"], 'username','Users')
        who_dis_text = "You are logged in as {} {}.".format(fname, lname)
        title = info_dict['title']
        author = info_dict['author']
        year = info_dict['year']
        n_reviews = info_dict['review_count']
        n_ratings = info_dict['average_score']
        rounded_rating = round(float(n_ratings))
        

    if request.method == "GET":
        if did_they_review_this(session["current_user"], isbn):
            all_reviews = get_reviews(isbn)
            return render_template('bookpage_submitted.html', rounded_rating = rounded_rating, all_reviews=all_reviews, isbn=isbn, title=title, author=author, year=year, n_reviews=n_reviews, n_ratings=n_ratings, who_dis_text=who_dis_text)
        else:
            all_reviews = get_reviews(isbn)
            return render_template('bookpage.html', rounded_rating = rounded_rating, all_reviews=all_reviews, isbn=isbn, title=title, author=author, year=year, n_reviews=n_reviews, n_ratings=n_ratings, who_dis_text=who_dis_text)

    else:
        req = request.form
        rating = req["rating"]
        review = req["review"]
        ins = Reviews.insert().values(username = session["current_user"], isbn = isbn, review = review, rating = rating )
        s.execute(ins)
        s.commit()
        all_reviews = get_reviews(isbn)
        return render_template('bookpage_submitted.html', rounded_rating = rounded_rating, all_reviews=all_reviews, isbn=isbn, title=title, author=author, year=year, n_reviews=n_reviews, n_ratings=n_ratings, who_dis_text=who_dis_text)

if __name__ == '__main__':
	app.run(debug = True)