"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, jsonify, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Movie, Rating


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# Normally, if you use an undefined variable in Jinja2, it fails
# silently. This is horrible. Fix this so that, instead, it raises an
# error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def index():
    """Homepage."""
    # a = jsonify([1,3])
    # return a
    return render_template("homepage.html")


@app.route("/users")
def user_list():
    """Show list of users."""

    users = User.query.all()
    return render_template("user_list.html", users=users)


@app.route("/movies")
def movie_list():
    """Show list of movies."""

    movies = Movie.query.all()
    movies = sorted([(movie.title, movie.movie_id) for movie in movies])
    return render_template("movie_list.html", movies=movies)


@app.route("/registration", methods=["GET"])
def registration_form():
    return render_template("registration_form.html")


@app.route("/registration", methods=["POST"])
def registration():
    """handles registration form"""

    email = request.form.get("email")
    password = request.form.get("password")
    age = request.form.get("age")
    gender = request.form.get("gender")
    zipcode = request.form.get("zip")

    user = User.query.filter(User.email == email).all()

    if user:
        flash("You have already registered! Please Sign In")
    else:
        user = User(email=email, password=password, age=age, gender=gender, zipcode=zipcode)
        db.session.add(user)
        db.session.commit()
        flash("You have been registered. Thank you.")
    return redirect("/")


@app.route("/check_login.json", methods=["POST"])
def check_login():
    email = request.form.get("email")
    password = request.form.get("password")

    user = User.query.filter(User.email == email).all()
    if user:

        if user[0].password == password:
            return jsonify({"success": "all good"})
        else:
            return jsonify({"success": "wrong password"})
    else:
        return jsonify({"success": "not registered"})


@app.route("/login", methods=["POST"])
def login():
    session["user_email"] = request.form.get("email")
    flash("Logged in as "+session["user_email"])
    user = User.query.filter(User.email == session["user_email"]).all()
    user_id = user[0].user_id
    session["user_id"] = user_id
    return redirect("/users/%d" % user_id)



@app.route("/login", methods=["GET"])
def login_page():

    return render_template("login.html")


@app.route("/logout")
def logout():
    del session["user_email"]
    del session["user_id"]
    flash("Logout successful")
    return redirect("/")

@app.route("/users/<user_id>")
def show_profile(user_id):
    user = User.query.filter(User.user_id == user_id).all()

    ratings = Rating.query.filter(Rating.user_id == user_id).options(db.joinedload('movie')).all()

    rating_titles=[]
    for rating in ratings:
        rating_titles.append((rating.score, rating.movie.title, rating.movie_id))



    return render_template("user-profile.html", email=user[0].email, age=user[0].age,
                            gender=user[0].gender,zipcode=user[0].zipcode, rating_titles=rating_titles)

@app.route("/movies/<movie_id>")
def show_movie(movie_id):
    movie = Movie.query.filter(Movie.movie_id == movie_id).all()

    ratings = Rating.query.filter(Rating.movie_id == movie_id).all()

    rating_user_id=[]
    for rating in ratings:
        rating_user_id.append((rating.score, rating.user_id))

    year = movie[0].released_at.year


    return render_template("movie-profile.html", title=movie[0].title, movie_id=movie[0].movie_id,
                           year=year, imdb_url=movie[0].imdb_url, rating_user_id=rating_user_id)

@app.route("/add-rating", methods=["POST"])
def add_rating():
    movie_id = request.form.get("movie")
    rating = request.form.get("score")

    user_id = session["user_id"]

    rating = Rating(movie_id=movie_id, score=rating, user_id=user_id)
    db.session.add(rating)
    db.session.commit()

    flash("Your rating has been added!")

    return redirect("/movies/%s" % movie_id)


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)



    app.run(port=5000, host='0.0.0.0')
