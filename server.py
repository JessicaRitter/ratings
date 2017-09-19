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

    user = User.query.filter(User.email == email).all()

    if user:
        flash("You have already registered! Please Sign In")
    else:
        user = User(email=email, password=password, age=age, gender=gender)
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
    return redirect("/")



@app.route("/login", methods=["GET"])
def login_page():

    return render_template("login.html")

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the
    # point that we invoke the DebugToolbarExtension
    app.debug = True
    app.jinja_env.auto_reload = app.debug  # make sure templates, etc. are not cached in debug mode

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)



    app.run(port=5000, host='0.0.0.0')
