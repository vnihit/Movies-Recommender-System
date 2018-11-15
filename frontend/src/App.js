import React, { Component } from 'react';
import { Divider, AutoComplete, Input, Icon, Button, Tooltip, notification, Slider } from 'antd';
import './App.css';
import logo from "./img/logo.png";

class MovieImage extends Component {
  state = {
    loading: true
  }

  render() {
    const { poster, alt } = this.props;
    const { loading } = this.state;

    return (
      <div className="poster">
        {loading && <Icon type="loading" />}
        <img
          src={`https://image.tmdb.org/t/p/original/${poster}`}
          alt={alt}
          style={{ display: loading ? "none" : "block" }}
          onLoad={() => this.setState({ loading: false })}
        />
      </div>
    )
  }
}

class App extends Component {
  state = {
    searching: false,
    recommending: false,
    movies: [],
    options: [],
    favourites: [],
    recommendations: [],
    marks: [1900, 2017]
  };

  queryMovies = query => {
    if (!query) {
      this.setState({ movies: [], options: [], query: null });
      return;
    };

    this.setState({ searching: true, query });

    fetch(`http://localhost:8000/movies/movie_by_title/?q=${query}`)
      .then(response => {
        response.json().then(movies => {
          this.setState({
            searching: false,
            movies,
            options: movies.map(movie => {
              const releaseDate = new Date(movie.release_date);

              return (
                <AutoComplete.Option key={movie.id} value={movie.id.toString()} label={movie.name}>
                  <div className="card">
                    <MovieImage poster={movie.poster} alt={movie.title} />
                    <div className="content">
                      <div className="title">
                        {movie.title} ({releaseDate.getFullYear()})
                      </div>
                      <p>
                        {movie.overview.length > 250 ? `${movie.overview.slice(0, 250)} ...` : movie.overview}
                      </p>
                    </div>
                  </div>
                </AutoComplete.Option>
              )
            })
          });
        });
      });
  };

  addToFavourites = selectedMovieId => {
    const { movies, favourites } = this.state;

    const movieId = parseInt(selectedMovieId);
    if (favourites.find(favourite => favourite.id === movieId))
      return;

    const movie = movies.find(movie => movie.id === movieId);
    this.setState({ query: null, movies: [], options: [], favourites: [...favourites, movie] });
  }
  
  removeFromFavourites = selectedMovieId => {
    const { favourites } = this.state;
    this.setState({ favourites: favourites.filter(favourite => favourite.id !== selectedMovieId) })
  }

  recommendMovies = () => {
    const { favourites, marks } = this.state;

    if (favourites.length === 0) {
      notification.error({
        message: 'No favourites chosen!',
        description: 'You must favourite at least one movie in order to receive recommendations.',
      });
      return;
    }

    this.setState({ recommending: true });

    fetch(`http://localhost:8000/movies/recommend_movies/`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        favourites: favourites.map(favourite => favourite.id),
        years: marks
      })
    })
      .then(response => {
        response.json().then(recommendations => {
          this.setState({
            recommending: false,
            recommendations 
          });
        });
      });
  };

  MovieCard = (movie, isFavourite) => {
    const releaseDate = new Date(movie.release_date);

    return (
      <div className="movie-card" key={movie.id}>
        <MovieImage poster={movie.poster} alt={movie.title} />
        <div className="content">
          <div className="title">
            {movie.title} ({releaseDate.getFullYear()})
          </div>
          <div className="info">
            <span>Genre:</span>
            {movie.genres.split(",").join(", ")}
            <span style={{ marginLeft: 15 }}>Rating:</span>
            {movie.vote_average}/10
            <span style={{ marginLeft: 15 }}>Runtime:</span>
            {movie.runtime} mins
          </div>
          <div className="info">
            <span>Cast:</span>
            {movie.cast.split(",").slice(0, 3).join(", ")}
            <span style={{ marginLeft: 15 }}>Director:</span>
            {movie.directors.split(",").slice(0, 3).join(", ")}
          </div>
          <div className="overview">
            {movie.overview}
          </div>
          { isFavourite &&
            <Tooltip title="Remove from favourites">
              <Icon 
                className="star"
                type="star" 
                theme="filled" 
                onClick={() => this.removeFromFavourites(movie.id)}
              />
            </Tooltip>
          }
        </div>
      </div>
    )
  };

  render() {
    const { searching, options, query, favourites, recommending, recommendations, marks } = this.state;

    return (
      <div className="app">
        <header className="header">
          <img src={logo} style={{ maxWidth: 300, margin: "10px 0 20px" }}/>
          <div>Get recommendations based on your favourite movies.</div>
        </header>

        <Divider />

        <div>
          <Tooltip title={favourites.length === 5 ? "Only 5 movies can be favourited" : ""}>
            <AutoComplete
              size="large"
              style={{ width: '100%' }}
              placeholder="Start typing a movie title..."
              onSearch={e => this.queryMovies(e)}
              dataSource={options}
              onSelect={e => this.addToFavourites(e)}
              value={query}
              disabled={favourites.length === 5}
            >
              <Input suffix={searching ? <Icon type="loading" /> : <Icon type="search" />} />
            </AutoComplete>
          </Tooltip>
        </div>

        <h2 style={{ marginTop: 30, color: "#E8EAF6" }}>
          Your favourite movies
        </h2>

        <div className="movie-list">
          { favourites.length === 0 ?
            <div className="placeholder">
              Search above to add your first movie
            </div>
          :
            favourites.map(favourite =>
              this.MovieCard(favourite, true)
            )
          }
        </div>

        <h2 style={{ marginTop: 30, color: "#E8EAF6" }}>
          Movies you might like
        </h2>

        <div className="recommended">
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", marginBottom: 15 }}>
            <Button 
              loading={recommending}
              size="large" 
              icon="experiment" 
              type="primary" 
              onClick={() => this.recommendMovies()}
            >
              Recommend
            </Button>

            <div style={{ display: "flex", alignItems: "center", width: "100%", margin: "0 15px" }}>
              <span style={{ margin: "0 15px", color: "white" }}>
                Filter results by year:
              </span>
              <Slider 
                range
                size="large" 
                defaultValue={[1900, 2017]} 
                min={1900} 
                max={2017} 
                style={{ flex: 1, margin: "0 0 0 10px" }} 
                marks={{ 
                  [marks[0]]: { style: { color: "white" }, label: marks[0] }, 
                  [marks[1]]: { style: { color: "white" }, label: marks[1] }
                }}
                onAfterChange={marks => this.setState({ marks })}
              />
            </div>
          </div>

          { recommendations.length > 0 &&
            <div className="movie-list">
              {recommendations.map(movie =>
                this.MovieCard(movie, false)
              )}
            </div>
          }
        </div>
      </div>
    );
  }
}

export default App;
