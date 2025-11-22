import requests
import time
import json
import os
from typing import Dict, List, Optional
from config import OMDB_API_KEY, OMDB_BASE_URL

class MovieAPIHandler:
    def __init__(self):
        self.omdb_api_key = OMDB_API_KEY
        self.cache_dir = "cache"
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _get_cache_path(self, movie_title: str) -> str:
        """Generate cache file path for a movie"""
        import hashlib
        filename = hashlib.md5(movie_title.lower().encode()).hexdigest() + ".json"
        return os.path.join(self.cache_dir, filename)
    
    def _load_from_cache(self, movie_title: str) -> Optional[Dict]:
        """Load movie data from cache"""
        cache_path = self._get_cache_path(movie_title)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None
    
    def _save_to_cache(self, movie_title: str, data: Dict):
        """Save movie data to cache"""
        cache_path = self._get_cache_path(movie_title)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def search_movie_omdb(self, movie_title: str) -> Optional[Dict]:
        """Search for movie using OMDb API"""
        if not self.omdb_api_key or self.omdb_api_key == "4bcd5aba":
            return None
            
        # Check cache first
        cached_data = self._load_from_cache(movie_title)
        if cached_data and 'omdb' in cached_data:
            return cached_data['omdb']
        
        try:
            params = {
                'apikey': self.omdb_api_key,
                't': movie_title,
                'type': 'movie',
                'plot': 'short'
            }
            
            response = requests.get(OMDB_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('Response') == 'True':
                # Cache the result
                self._save_to_cache(movie_title, {'omdb': data})
                return data
                
        except requests.exceptions.RequestException as e:
            print(f"OMDb API error for '{movie_title}': {e}")
        except Exception as e:
            print(f"Unexpected error with OMDb for '{movie_title}': {e}")
            
        return None
    
    def get_movie_data(self, movie_title: str) -> Dict:
        """Get movie data from OMDb API"""
        movie_data = {}
        
        # Try OMDb
        omdb_data = self.search_movie_omdb(movie_title)
        if omdb_data:
            movie_data['omdb'] = omdb_data
            movie_data['title'] = omdb_data.get('Title', movie_title)
            movie_data['genres'] = omdb_data.get('Genre', '').split(', ') if omdb_data.get('Genre') else []
            movie_data['year'] = omdb_data.get('Year', 'Unknown').replace('–', '').split('–')[0]
            movie_data['overview'] = omdb_data.get('Plot', '')
            movie_data['rating'] = omdb_data.get('imdbRating')
            movie_data['source'] = 'OMDb'
        
        # If no API data found, create minimal data
        if not movie_data:
            movie_data = {
                'title': movie_title,
                'genres': ['Unknown'],
                'year': 'Unknown',
                'overview': 'No information available',
                'rating': None,
                'source': 'Not Found'
            }
        
        return movie_data