import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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


@app.route("/")
def index():
    # return "Project 1: TODO"
    session["user"] = None
    return render_template("login.html")


@app.route("/homepage", methods=["GET", "POST"])
def homepage():
    username = request.form.get("username")
    passwords = request.form.get("password")
    if session["user"] is not None:
        return render_template("homepage.html", user=session["user"].username)         
    if username is None or passwords is None:
        return render_template("error.html", message="Please login first to go to the homepage!")
    elif username=="":
        return render_template("error.html", message="You did not type in any username, please try again!")
    elif passwords=="":
        return render_template("error.html", message="You did not type in any password, please try again!")
    account = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
    if account is None:
        return render_template("error.html", message="Account not found.")
    if account.passwords == passwords:
        session["user"] = account
        return render_template("homepage.html", user=session["user"].username)
    else:
        return render_template("error.html", message="You typed in the wrong password")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username=="":
            return render_template("error.html", message="You did not type in any username, please try again!")
        elif password=="":
            return render_template("error.html", message="You did not type in any password, please try again!")
        existed_username = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchone()
        if existed_username is not None:
            return render_template("error.html", message="This username has been used before, please use another username!")        
        db.execute("INSERT INTO users (username, passwords) VALUES (:username, :passwords)", {"username": username, "passwords": password})
        db.commit()
        return render_template("register_success.html")

    return render_template("register.html")
    # TODO: Create register error message html that can direct back to the register page instead of login page


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session["user"] = None
    return redirect(url_for("index"))

@app.route("/booksearch", methods=['POST'])
def search():
    search_name = request.form.get("search")
    if search_name == "" or search_name is None:
        return render_template("homepage.html", user=session["user"].username)
    book_lists = db.execute("SELECT * FROM books WHERE ISBN ILIKE :search1 OR ISBN ILIKE :search2 OR ISBN ILIKE :search3 OR title ILIKE :search1 OR title ILIKE :search2 OR title ILIKE :search3 OR author ILIKE :search1 OR author ILIKE :search2 OR author ILIKE :search3", {"search1": '%'+search_name+'%', "search2": '%'+search_name, "search3": search_name+'%'}).fetchall()
    if len(book_lists) == 0:
        return render_template("search_notfound.html", user=session["user"].username, message="Sorry, your book is not found..")
    return render_template("booksearch.html", user=session["user"].username, book_lists = book_lists)

@app.route("/bookpage/<string:isbn>", methods=['POST'])
def bookpage(isbn):
    user_reviews = []
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return render_template("error.html", message="Sorry, your book is not found")
    reviews = db.execute("SELECT * FROM reviews WHERE book_id=:book_id", {"book_id":book.id}).fetchall()
    for review in reviews:
        user_reviews.append((review.rating, review.content))



    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "YAVDzaUp2yefaerdI9NyQ", "isbns": book.isbn})
    if res.status_code != 200:
        goodread_average = "No available goodread average rating yet.."
        goodread_count = "No goodread rating for this book yet..."
    else: 
        goodread_rating = res.json()
        goodread_average = goodread_rating['books'][0]['average_rating']
        goodread_count = goodread_rating['books'][0]['work_ratings_count']
        
    



    if request.method == "POST" and "your_ratings" in request.form:
        received_ratings = request.form.get("your_ratings")
        received_reviews = request.form.get("your_reviews")
        existed_review = db.execute("SELECT * FROM reviews WHERE userid=:user AND book_id=:book", {"user": session["user"].id, "book": book.id}).fetchone()
        if existed_review is not None:
            return render_template("error.html", message="Sorry, you have already written a review for this book, and can not write another one for the same book")
        if received_ratings is None:
            return render_template("error.html", message="Sorry, you must submit a rating score")
        elif received_reviews is None:
            return render_template("error.html", message="Sorry, you must submit review contents")

        db.execute("INSERT INTO reviews (rating, content, userid, book_id) VALUES (:rating, :content, :user, :book_id)", {"rating": received_ratings, "content": received_reviews, "user": session["user"].id, "book_id": book.id})
        db.commit()
        new_review = db.execute("SELECT * FROM reviews WHERE userid=:user AND book_id=:book", {"user": session["user"].id, "book": book.id}).fetchone()
        if new_review is None:
            return render_template("error.html", message="Sorry, your review failed to be uploaded, please try again!")
        user_reviews.append((new_review.rating, new_review.content))


    return render_template("bookpage.html", isbn=book.isbn, title= book.title, author=book.author, year=book.publicationyear, user_reviews=user_reviews, goodread_average=goodread_average, goodread_count=goodread_count)



@app.route("/api/<string:isbn>")
def review_api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "ISBN number not found"}), 404
    reviews = db.execute("SELECT * FROM reviews WHERE book_id=:book_id", {"book_id": book.id}).fetchall()
    sum_review = 0 
    for review in reviews:
        sum_review += review.rating
    average_reviews = sum_review/max(1, len(reviews))

    return jsonify(
        {
            "title": book.title,
            "author": book.author,
            "year": book.publicationyear,
            "isbn": book.isbn,
            "review_count": len(reviews),
            "average_score": average_reviews
        }
    )
