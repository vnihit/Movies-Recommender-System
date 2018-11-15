from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.conf import settings

import pandas as pd
from datetime import date
import ast
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Movie
from .serializers import MovieSerializer


class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieSerializer

    def merge_data(self):
        movies = pd.read_csv("seed/movies_metadata.csv", low_memory=False)
        movies["id"] = movies["id"].apply(pd.to_numeric, errors="coerce")

        keywords = pd.read_csv("seed/keywords.csv", low_memory=False)
        keywords["id"] = keywords["id"].apply(pd.to_numeric, errors="coerce")

        movie_credits = pd.read_csv("seed/credits.csv", low_memory=False)
        movie_credits["id"] = movie_credits["id"].apply(pd.to_numeric, errors="coerce")

        movies = movies.merge(keywords, on="id")
        movies = movies.merge(movie_credits, on="id")

        return movies

    def clean_data(self, movies):
        features = [
            "id",
            "imdb_id",
            "title",
            "overview",
            "poster_path",
            "runtime",
            "vote_average",
            "vote_count",
            "release_date",
            "genres",
            "production_companies",
            "keywords",
            "cast",
            "crew",
        ]
        movies = movies[features]
            
        movies.dropna(inplace=True)

        # Ignore movies lower than the minimum number of votes
        movies.drop(movies[movies.vote_count < 100].index, inplace=True)

        return movies

    @action(detail=False, methods=["get"])
    def bulk_create(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise PermissionDenied(detail="Bulk create can only be performed in debug mode")

        Movie.objects.all().delete()
        count = 1

        def stringify_list(values, skip_eval=False):
            if not skip_eval:
                values = ast.literal_eval(values)
            # Consider only the first 3 values of the list
            values = values[:3]
            mapped_values = map(lambda x: x["name"], values)
            return ",".join(list(mapped_values))

        movies = self.merge_data()
        movies = self.clean_data(movies)
        number_of_movies = len(movies.index)

        for index, item in movies.iterrows():
            movie = Movie(
                title=item["title"],
                overview=item["overview"],
                poster=item["poster_path"],
                runtime=item["runtime"],
                vote_average=item["vote_average"],
                release_date=date(*map(int, item["release_date"].split("-"))),
                keywords=stringify_list(item["keywords"]),
                genres=stringify_list(item["genres"]),
                production_companies=stringify_list(item["production_companies"]),
                cast=stringify_list(item["cast"]),
                directors=stringify_list(
                    list(filter(lambda x: x["job"] == "Director", ast.literal_eval(item["crew"]))),
                    skip_eval=True
                )
            )

            soup = ",".join([movie.keywords, movie.cast, movie.directors,  movie.genres])
            movie.soup = str.lower(soup).replace(" ", "").replace(",", " ")
            
            movie.save()
            
            print(f'Imported "{movie.title}" ({count} of {number_of_movies})')
            count += 1

        return Response("Bulk create successfully completed")

    @action(detail=False, methods=["get"])
    def movie_by_title(self, request, *args, **kwargs):
        title_query = request.GET.get('q', '')
        if not len(title_query) > 0:
            raise ValidationError("Title cannot be empty")

        start_from = request.GET.get('from', 0)
        count = request.GET.get('count', 5)
        try:
            start_from = int(start_from)
            count = int(count)
        except ValueError:
           raise ValidationError("Invalid query")

        # Force a limit on the query count
        count = min(count, 25)

        # Case insensitive query against movie title
        # Only take the top 
        matching_movies = Movie.objects.filter(title__icontains=title_query)[start_from:start_from+count]

        # Serialize the results
        serializer = MovieSerializer(matching_movies, many=True)

        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def recommend_movies(self, request, *args, **kwargs):
        favourites = request.data["favourites"]
        years = request.data["years"]

        if len(favourites) < 1:
            raise ValidationError("At least one favourite movie is required")

        # Compute the count matrix across the entire corpus (all movies in the database)
        # Get movies in the user-defined year range, excluding those in the favourites
        movies = list(
            Movie.objects.filter(release_date__range=[f"{years[0]}-01-01", f"{years[1]}-12-31"],).exclude(id__in=favourites)
        )

        # Add the favourites to the movie list
        movies.extend(list(Movie.objects.filter(id__in=favourites)))

        df = pd.DataFrame([{ "id": movie.id, "soup": movie.soup } for movie in movies])

        vectorizer = CountVectorizer(stop_words='english')
        count_matrix = vectorizer.fit_transform(df['soup'])
        cosine_sim = cosine_similarity(count_matrix, count_matrix)

        movies_per_favourite = 15 // len(favourites)

        related_movies = set()

        for movie_id in favourites:
            # Get the index of the movie in the dataframe (different from the movie id)
            idx = df[df['id'] == movie_id].index[0]

            # Get the cosine similarity values for this movie against all other movies
            sim_scores = list(enumerate(cosine_sim[idx]))

            # Sort by cosine similarity value (highest first)
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

            # Take the top N movies based on the number of favourites specified
            # Ignore the first index, which is always the movie itself (with a correlation of 1)
            sim_scores = sim_scores[1:movies_per_favourite]

            # Get the movie id's from the dataframe id for each of the top related movies
            sim_scores = [(df.at[sim_score[0], "id"], sim_score[1]) for sim_score in sim_scores]

            # Add these movies to the set of related movies (prevent duplicates)
            related_movies.update(sim_scores)

        # Remove favourited movies from the list of related movies (if any)
        related_movies = list(filter(lambda x: x[0] not in favourites, related_movies))

        # Sort the total list of related movies and only take the top 10
        related_movies = list(sorted(related_movies, key=lambda x: x[1], reverse=True))[:10]

        # Get the movie object for each of the top related movies
        related_movies = [Movie.objects.get(id=related_movie[0]) for related_movie in related_movies]

        serializer = MovieSerializer(related_movies, many=True)

        return Response(serializer.data)
