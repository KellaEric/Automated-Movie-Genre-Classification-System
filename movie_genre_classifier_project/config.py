import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
# TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'your_tmdb_api_key_here')
OMDB_API_KEY = os.getenv('OMDB_API_KEY', '4bcd5aba')

# API Endpoints
# TMDB_BASE_URL = "https://api.themoviedb.org/3"
OMDB_BASE_URL = "http://www.omdbapi.com/?i=tt3896198&apikey=4bcd5aba"

# Default Settings
DEFAULT_GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", 
    "Documentary", "Drama", "Family", "Fantasy", "History",
    "Horror", "Music", "Mystery", "Romance", "Science Fiction",
    "TV Movie", "Thriller", "War", "Western"
]

CACHE_DURATION = 24 * 60 * 60  # 24 hours in seconds