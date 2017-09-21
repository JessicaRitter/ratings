"""Models and database functions for Ratings project."""

from flask_sqlalchemy import SQLAlchemy
from correlation import pearson, euclidean_similarity
import random

# This is the connection to the PostgreSQL database; we're getting this through
# the Flask-SQLAlchemy helper library. On this, we can find the `session`
# object, where we do most of our interactions (like committing, etc.)

db = SQLAlchemy()


##############################################################################
# Model definitions

class User(db.Model):
    """User of ratings website."""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
    password = db.Column(db.String(64), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    zipcode = db.Column(db.String(15), nullable=True)
    gender = db.Column(db.String(24), nullable=True)


    def predict_rating(self, movie):
        return predict_rating(self.user_id,movie, euclidean_similarity)


    def __repr__(self):
        """Provide helpful representation when printed."""

        return "<User user_id=%s email=%s>" % (self.user_id,
                                               self.email)


# Put your Movie and Rating model classes here.

class Movie(db.Model):
    """Movies"""
    __tablename__ = "movies"

    movie_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String(256), nullable=True)
    released_at = db.Column(db.DateTime, nullable=True)
    imdb_url = db.Column(db.String(500), nullable=True)


class Rating(db.Model):
    """Movies"""
    __tablename__ = "ratings"

    rating_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.movie_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)

    # Define relationship to user
    user = db.relationship("User",
                           backref=db.backref("ratings",
                                              order_by=rating_id))

    # Define relationship to movie
    movie = db.relationship("Movie",
                            backref=db.backref("ratings",
                                               order_by=rating_id))


##############################################################################
# Helper functions

def connect_to_db(app):
    """Connect the database to our Flask app."""

    # Configure to use our PstgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///ratings'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.app = app
    db.init_app(app)


def predict_rating(user_id, movie_id, procedure):

    pred_user = Rating.query.filter(Rating.user_id == user_id).all()

    pred_movie_score = {pred_rating.movie_id: pred_rating.score for pred_rating in pred_user}

    users = Rating.query.filter(Rating.movie_id == movie_id, Rating.user_id != user_id).all()
    procedure_list=[]

    for user in users:
        rating_list = Rating.query.filter(Rating.user_id == user.user_id).all()
        movie_score = {rating.movie_id: rating.score for rating in rating_list}
        intersection = list(set(movie_score.keys()) & set(pred_movie_score.keys()))

        if intersection:
            pairs = []
            for movie_id in intersection:
                pairs.append((pred_movie_score[movie_id],
                    movie_score[movie_id]))
            # print pairs
            # print procedure(pairs)
            procedure_list.append((procedure(pairs), movie_score[user.movie_id]))


    numerator = sum([(rating * coefficient) for coefficient, rating in procedure_list if coefficient > 0])
    denominator = sum([coefficient for coefficient, rating in procedure_list if coefficient > 0])
    # print numerator, denominator
    mean = numerator/denominator

    if mean > 5:
        mean = 5
    elif mean < 1:
        mean = 1
    return mean




if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app
    connect_to_db(app)
    print "Connected to DB."
