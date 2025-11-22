import pandas as pd
from typing import List, Dict, Any
from api_handler import MovieAPIHandler
from config import DEFAULT_GENRES
import time

class MovieGenreClassifier:
    def __init__(self):
        self.api_handler = MovieAPIHandler()
        self.processed_movies = []
    
    def classify_movies(self, movie_titles: List[str], progress_callback=None) -> Dict[str, Any]:
        """Classify a list of movies by genre"""
        classified_movies = {genre: [] for genre in DEFAULT_GENRES}
        classified_movies['Unknown'] = []
        self.processed_movies = []
        
        total_movies = len(movie_titles)
        
        for i, title in enumerate(movie_titles):
            if progress_callback:
                progress_callback(i + 1, total_movies)
            
            movie_data = self.api_handler.get_movie_data(title.strip())
            self.processed_movies.append(movie_data)
            
            # Add to genre categories
            genres = movie_data.get('genres', [])
            if not genres:
                classified_movies['Unknown'].append(movie_data)
            else:
                for genre in genres:
                    if genre in classified_movies:
                        classified_movies[genre].append(movie_data)
                    else:
                        classified_movies['Unknown'].append(movie_data)
            
            # Small delay to be respectful to APIs
            time.sleep(0.1)
        
        return classified_movies
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed movies"""
        if not self.processed_movies:
            return {}
        
        total_movies = len(self.processed_movies)
        found_movies = len([m for m in self.processed_movies if m.get('source') != 'Not Found'])
        unknown_genres = len([m for m in self.processed_movies if not m.get('genres') or m.get('genres') == ['Unknown']])
        
        genre_counts = {}
        for movie in self.processed_movies:
            for genre in movie.get('genres', []):
                if genre in genre_counts:
                    genre_counts[genre] += 1
                else:
                    genre_counts[genre] = 1
        
        return {
            'total_movies': total_movies,
            'found_movies': found_movies,
            'not_found_movies': total_movies - found_movies,
            'unknown_genres': unknown_genres,
            'genre_counts': genre_counts,
            'success_rate': (found_movies / total_movies) * 100 if total_movies > 0 else 0
        }
    
    def export_to_dataframe(self) -> pd.DataFrame:
        """Export processed movies to pandas DataFrame"""
        data = []
        for movie in self.processed_movies:
            data.append({
                'Title': movie.get('title', ''),
                'Year': movie.get('year', 'Unknown'),
                'Genres': ', '.join(movie.get('genres', [])),
                'Rating': movie.get('rating', 'N/A'),
                'Overview': movie.get('overview', ''),
                'Source': movie.get('source', 'Unknown')
            })
        
        return pd.DataFrame(data)