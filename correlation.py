"""Pearson correlation."""

from math import sqrt
# from model import connect_to_db, db, User, Movie, Rating


def pearson(pairs):
    """Return Pearson correlation for pairs.
    Using a set of pairwise ratings, produces a Pearson similarity rating.
    """

    series_1 = [float(pair[0]) for pair in pairs]
    series_2 = [float(pair[1]) for pair in pairs]

    sum_1 = sum(series_1)
    sum_2 = sum(series_2)

    squares_1 = sum([n * n for n in series_1])
    squares_2 = sum([n * n for n in series_2])

    product_sum = sum([n * m for n, m in pairs])

    size = len(pairs)

    numerator = product_sum - ((sum_1 * sum_2) / size)

    denominator = sqrt(
        (squares_1 - (sum_1 * sum_1) / size) *
        (squares_2 - (sum_2 * sum_2) / size)
    )

    if denominator == 0:
        return 0

    return numerator / denominator


def euclidean_similarity(pairs):

    return 1/(1+sqrt(sum([pow(item1 - item2, 2) for item1, item2 in pairs])))


# def predict_rating(user_id, movie_id):

#     pred_user = Rating.query.filter(Rating.user_id == user_id).all()

#     pred_movie_score = {pred_rating.movie_id: pred_rating.score for pred_rating in pred_user}

#     users = Rating.query.filter(Rating.movie_id == movie_id, Rating.user_id != user_id).all()
#     pearson_list=[]
#     for user in users:
#         rating_list = Rating.query.filter(Rating.user_id == user.user_id).all()
#         movie_score = {rating.movie_id: rating.score for rating in rating_list}
#         intersection = list(set(movie_score.keys()) & set(pred_movie_score.keys()))
#         if intersection:
#             pairs = []
#             for movie_id in pred_movie_score.keys():
#                 pairs.append((pred_movie_score[movie_id],movie_score.get(movie_id,3)))
#             pearson_list.append(pearson(pairs))
#         else:
#             pearson_list.append(0)

#     max_position = pearson_list.index(max(pearson_list))
#     best_user = users[max_position]

#     return best_user

