"""Movie Ratings."""

from jinja2 import StrictUndefined

from flask import Flask, jsonify, render_template, redirect, request, flash, session
from flask_debugtoolbar import DebugToolbarExtension

from model import connect_to_db, db, User, Movie, Rating
import correlation
import random

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
    return redirect("/login")


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


    if (session.get("user_id", None) and
        len(Rating.query.filter(Rating.user_id == session["user_id"]).all()) > 5
        and not Rating.query.filter(Rating.user_id == session["user_id"], Rating.movie_id == movie_id).all()):
        predrating = round(User.query.filter(User.user_id == session["user_id"]).one().predict_rating(movie_id))
    elif not (session.get("user_id", None) or
        len(Rating.query.filter(Rating.user_id == session["user_id"]).all()) > 5):
        predrating = -1
    else:
        predrating = Rating.query.filter(Rating.user_id == session["user_id"], Rating.movie_id == movie_id).all()[0].score



    the_eye = (User.query.filter_by(email="the-eye@of-judgment.com")
                         .one())
    eye_rating = Rating.query.filter_by(
        user_id=the_eye.user_id, movie_id=movie_id).first()


    if eye_rating is None:
        eye_rating = the_eye.predict_rating(movie_id)

    else:
        eye_rating = eye_rating.score

    if eye_rating and predrating:
        difference = abs(eye_rating - predrating)

    else:
        # We couldn't get an eye rating, so we'll skip difference
        difference = None

    BERATEMENT_MESSAGES = [
        "I suppose you don't have such bad taste after all.",
        "I regret every decision that I've ever made that has " +
            "brought me to listen to your opinion.",
        "Words fail me, as your taste in movies has clearly " +
            "failed you.",
        "That movie is great. For a clown to watch. Idiot.",
        "Words cannot express the awfulness of your taste."
    ]

    if difference is not None:
        beratement = BERATEMENT_MESSAGES[int(difference)]

    else:
        beratement = None

    return render_template("movie-profile.html", title=movie[0].title, movie_id=movie[0].movie_id,
                           year=year, imdb_url=movie[0].imdb_url, rating_user_id=rating_user_id, predrating=predrating,
                           beratement=beratement)


@app.route("/add-rating", methods=["POST"])
def add_rating():
    movie_id = request.form.get("movie")
    rating_score = request.form.get("score")

    user_id = session["user_id"]
    rating = Rating.query.filter(Rating.user_id == user_id, Rating.movie_id == movie_id).all()
    if rating:
       rating[0].score = rating_score
    else:
        rating = Rating(movie_id=movie_id, score=rating_score, user_id=user_id)
        db.session.add(rating)
    db.session.commit()

    flash("Your rating has been added!")

    return redirect("/movies/%s" % movie_id)


@app.route("/test")
def test_pearson():
    random_users = random.sample(Rating.query.filter(Rating.movie_id == 346).all(),25)
    with open("test.txt","w") as f:
        for random_user in random_users:
            predrating = User.query.filter(User.user_id ==random_user.user_id).one().predict_rating(346)
            print "predicted score for user " , predrating
            print "actual score for user", random_user.score
            print "user_id", random_user.user_id
            f.write(str(predrating)+"|"+str(random_user.score)+"|"+str(random_user.user_id)+"\n")

    return "Done"


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)



    app.run(port=5000, host='0.0.0.0')
