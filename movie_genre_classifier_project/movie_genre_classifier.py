# app.py - Complete Single File Movie Genre Classifier with OMDb API
import streamlit as st
import pandas as pd
import requests
import json
import csv
import time
import os
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional
from io import StringIO

# Page configuration
st.set_page_config(
    page_title="Automated Movie Genre Classifier",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .genre-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 0.5rem 0;
    }
    .stat-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .movie-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-left: 4px solid #1f77b4;
        background-color: #f8f9fa;
    }
    .rating-excellent { color: #00ff00; font-weight: bold; }
    .rating-good { color: #aaff00; font-weight: bold; }
    .rating-average { color: #ffff00; font-weight: bold; }
    .rating-poor { color: #ffaa00; font-weight: bold; }
    .rating-bad { color: #ff0000; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

class MovieGenreClassifier:
    def __init__(self):
        # Your OMDb API key directly implemented
        self.omdb_api_key = "4bcd5aba"
        
        self.default_genres = [
            "Action", "Adventure", "Animation", "Comedy", "Crime", 
            "Documentary", "Drama", "Family", "Fantasy", "History",
            "Horror", "Music", "Mystery", "Romance", "Science Fiction",
            "Thriller", "War", "Western", "Unknown"
        ]
        self.processed_movies = []
        
    def search_movie_omdb(self, movie_title: str) -> Optional[Dict]:
        """Search for movie using OMDb API"""
        try:
            params = {
                'apikey': self.omdb_api_key,
                't': movie_title,
                'type': 'movie',
                'plot': 'short'
            }
            
            response = requests.get("http://www.omdbapi.com/", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('Response') == 'True':
                return data
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            st.sidebar.warning(f"OMDb API error for '{movie_title}': {e}")
        except Exception as e:
            st.sidebar.warning(f"Unexpected error with OMDb for '{movie_title}': {e}")
            
        return None
    
    def get_movie_data(self, movie_title: str) -> Dict:
        """Get movie data from OMDb API"""
        movie_data = {}
        
        # Try OMDb API
        omdb_data = self.search_movie_omdb(movie_title)
        if omdb_data:
            movie_data['omdb'] = omdb_data
            movie_data['title'] = omdb_data.get('Title', movie_title)
            movie_data['genres'] = omdb_data.get('Genre', '').split(', ') if omdb_data.get('Genre') else []
            movie_data['year'] = omdb_data.get('Year', 'Unknown').replace('–', '').split('–')[0]
            movie_data['overview'] = omdb_data.get('Plot', '')
            movie_data['rating'] = omdb_data.get('imdbRating')
            movie_data['votes'] = omdb_data.get('imdbVotes', '0').replace(',', '')
            movie_data['director'] = omdb_data.get('Director', 'Unknown')
            movie_data['actors'] = omdb_data.get('Actors', 'Unknown')
            movie_data['runtime'] = omdb_data.get('Runtime', 'Unknown')
            movie_data['box_office'] = omdb_data.get('BoxOffice', 'Unknown')
            movie_data['poster'] = omdb_data.get('Poster', '')
            movie_data['metascore'] = omdb_data.get('Metascore', 'N/A')
            movie_data['source'] = 'OMDb'
        
        # If no API data found, create minimal data
        if not movie_data:
            movie_data = {
                'title': movie_title,
                'genres': ['Unknown'],
                'year': 'Unknown',
                'overview': 'No information available',
                'rating': None,
                'votes': '0',
                'director': 'Unknown',
                'actors': 'Unknown',
                'runtime': 'Unknown',
                'box_office': 'Unknown',
                'poster': '',
                'metascore': 'N/A',
                'source': 'Not Found'
            }
        
        return movie_data

    def search_single_movie(self, movie_title: str) -> Dict:
        """Search for a single movie and return detailed results"""
        return self.get_movie_data(movie_title)
    
    def classify_movies(self, movie_titles: List[str], progress_callback=None) -> Dict[str, Any]:
        """Classify a list of movies by genre"""
        classified_movies = {genre: [] for genre in self.default_genres}
        self.processed_movies = []
        
        total_movies = len(movie_titles)
        
        for i, title in enumerate(movie_titles):
            if progress_callback:
                progress_callback(i + 1, total_movies)
            
            movie_data = self.get_movie_data(title.strip())
            self.processed_movies.append(movie_data)
            
            # Add to genre categories
            genres = movie_data.get('genres', [])
            if not genres or genres == ['Unknown']:
                classified_movies['Unknown'].append(movie_data)
            else:
                for genre in genres:
                    if genre in classified_movies:
                        classified_movies[genre].append(movie_data)
                    else:
                        classified_movies['Unknown'].append(movie_data)
            
            # Small delay to be respectful to API
            time.sleep(0.2)
        
        return classified_movies
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about processed movies"""
        if not self.processed_movies:
            return {}
        
        total_movies = len(self.processed_movies)
        found_movies = len([m for m in self.processed_movies if m.get('source') != 'Not Found'])
        unknown_genres = len([m for m in self.processed_movies if not m.get('genres') or m.get('genres') == ['Unknown']])
        
        genre_counts = {}
        rating_data = []
        rating_categories = {'Excellent (9-10)': 0, 'Good (7-8.9)': 0, 'Average (5-6.9)': 0, 'Poor (3-4.9)': 0, 'Bad (0-2.9)': 0}
        
        for movie in self.processed_movies:
            # Genre counts
            for genre in movie.get('genres', []):
                if genre in genre_counts:
                    genre_counts[genre] += 1
                else:
                    genre_counts[genre] = 1
            
            # Rating analysis
            if movie.get('source') != 'Not Found' and movie.get('rating') and movie.get('rating') != 'N/A':
                try:
                    rating = float(movie.get('rating'))
                    rating_data.append(rating)
                    
                    # Categorize ratings
                    if rating >= 9:
                        rating_categories['Excellent (9-10)'] += 1
                    elif rating >= 7:
                        rating_categories['Good (7-8.9)'] += 1
                    elif rating >= 5:
                        rating_categories['Average (5-6.9)'] += 1
                    elif rating >= 3:
                        rating_categories['Poor (3-4.9)'] += 1
                    else:
                        rating_categories['Bad (0-2.9)'] += 1
                except:
                    pass
        
        # Calculate average rating for found movies
        avg_rating = sum(rating_data) / len(rating_data) if rating_data else 0
        
        # Get top rated movies
        rated_movies = [m for m in self.processed_movies if m.get('rating') and m.get('rating') != 'N/A' and m.get('source') != 'Not Found']
        top_rated_movies = sorted(rated_movies, key=lambda x: float(x.get('rating', 0)), reverse=True)[:5]
        
        return {
            'total_movies': total_movies,
            'found_movies': found_movies,
            'not_found_movies': total_movies - found_movies,
            'unknown_genres': unknown_genres,
            'genre_counts': genre_counts,
            'success_rate': (found_movies / total_movies) * 100 if total_movies > 0 else 0,
            'average_rating': round(avg_rating, 2) if avg_rating else 0,
            'rating_data': rating_data,
            'rating_categories': rating_categories,
            'top_rated_movies': top_rated_movies,
            'total_ratings': len(rating_data)
        }

def get_rating_class(rating):
    """Get CSS class for rating display"""
    if not rating or rating == 'N/A':
        return ""
    try:
        rating_val = float(rating)
        if rating_val >= 8:
            return "rating-excellent"
        elif rating_val >= 7:
            return "rating-good"
        elif rating_val >= 6:
            return "rating-average"
        elif rating_val >= 5:
            return "rating-poor"
        else:
            return "rating-bad"
    except:
        return ""

def load_movies_from_file(uploaded_file) -> List[str]:
    """Load movie titles from various file formats"""
    movie_titles = []
    
    try:
        if uploaded_file.name.endswith('.csv'):
            # Read CSV file
            df = pd.read_csv(uploaded_file)
            # Assume first column contains movie titles
            movie_titles = df.iloc[:, 0].dropna().astype(str).tolist()
            
        elif uploaded_file.name.endswith('.txt'):
            # Read text file
            content = uploaded_file.getvalue().decode("utf-8")
            movie_titles = [line.strip() for line in content.split('\n') if line.strip()]
                
        elif uploaded_file.name.endswith('.json'):
            # Read JSON file
            content = uploaded_file.getvalue().decode("utf-8")
            data = json.loads(content)
            if isinstance(data, list):
                movie_titles = [item if isinstance(item, str) else str(item) for item in data]
            elif isinstance(data, dict):
                # Try to extract titles from common keys
                for key in ['movies', 'titles', 'items']:
                    if key in data and isinstance(data[key], list):
                        movie_titles = [item if isinstance(item, str) else str(item) for item in data[key]]
                        break
                
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
    
    return movie_titles

def validate_movie_titles(movie_titles: List[str]) -> tuple:
    """Validate and clean movie titles"""
    valid_titles = []
    invalid_titles = []
    
    for title in movie_titles:
        cleaned_title = title.strip()
        if cleaned_title and len(cleaned_title) >= 1:
            valid_titles.append(cleaned_title)
        else:
            invalid_titles.append(title)
    
    return valid_titles, invalid_titles

def render_single_movie_search(classifier):
    """Render single movie search functionality"""
    st.subheader("🔍 Search Single Movie")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_title = st.text_input("Enter movie title to search:", placeholder="e.g., The Shawshank Redemption")
    
    with col2:
        search_clicked = st.button("🔎 Search Movie", use_container_width=True)
    
    if search_clicked and search_title:
        with st.spinner("Searching for movie..."):
            movie_data = classifier.search_single_movie(search_title)
            
            if movie_data and movie_data.get('source') != 'Not Found':
                st.success(f"✅ Found: {movie_data.get('title')} ({movie_data.get('year')})")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Movie details
                    st.write(f"**🎬 {movie_data.get('title')}** ({movie_data.get('year')})")
                    
                    # Rating with color coding
                    rating = movie_data.get('rating')
                    rating_class = get_rating_class(rating)
                    if rating and rating != 'N/A':
                        st.markdown(f"<div class='{rating_class}'>⭐ **IMDb Rating: {rating}/10**</div>", unsafe_allow_html=True)
                    
                    if movie_data.get('metascore') and movie_data.get('metascore') != 'N/A':
                        st.write(f"🎯 **Metascore: {movie_data.get('metascore')}**")
                    
                    st.write(f"**Genre:** {', '.join(movie_data.get('genres', []))}")
                    st.write(f"**Director:** {movie_data.get('director')}")
                    st.write(f"**Cast:** {movie_data.get('actors')}")
                    st.write(f"**Runtime:** {movie_data.get('runtime')}")
                    
                    if movie_data.get('box_office') and movie_data.get('box_office') != 'Unknown':
                        st.write(f"**Box Office:** {movie_data.get('box_office')}")
                    
                    if movie_data.get('overview'):
                        st.write(f"**Plot:** {movie_data.get('overview')}")
                
                with col2:
                    # Poster
                    poster_url = movie_data.get('poster', '')
                    if poster_url and poster_url != 'N/A':
                        st.image(poster_url, width=200)
                    else:
                        st.info("No poster available")
                
                st.markdown("---")
            else:
                st.error(f"❌ Movie '{search_title}' not found in OMDb database")

# def render_welcome_screen():
#     """Render welcome screen with instructions"""
#     col1, col2 = st.columns([2, 1])
    
#     with col1:
#         st.subheader("🎬 Welcome to the Movie Genre Classifier!")
#         st.markdown("""
#         This system automatically classifies movies into genres using information from OMDb API.
        
#         ### 🚀 How to use:
#         1. **Search individual movies** using the search feature
#         2. **Enter movie titles** manually OR **upload a file** (TXT, CSV, or JSON)
#         3. Click the **"Classify Movies"** button
#         4. View the results organized by genre with detailed analytics
#         5. Export your classified movie list
        
#         ### 📁 Supported Input Formats:
#         - **TXT file**: One movie title per line
#         - **CSV file**: Movie titles in the first column
#         - **JSON file**: Array of movie titles or object with 'movies' key
        
#         ### ✨ Features:
#         ✅ Individual movie search  
#         ✅ Automatic genre classification using OMDb API  
#         ✅ Complete movie metadata extraction  
#         ✅ Advanced rating analysis and visualizations  
#         ✅ Multiple export formats (CSV, JSON, Excel)  
#         ✅ Progress tracking  
#         ✅ Beautiful interface
#         """)
        
        st.success("🔑 **API Status: OMDb API Key Successfully Configured!**")
    
    with col2:
        st.subheader("📋 Sample Data")
        sample_movies = [
            "The Shawshank Redemption",
            "The Godfather",
            "The Dark Knight",
            "Pulp Fiction",
            "Forrest Gump",
            "Inception",
            "The Matrix",
            "Goodfellas",
            "The Avengers",
            "Titanic"
        ]
        
        # Create sample files
        sample_csv = "Movie Title\n" + "\n".join(sample_movies)
        sample_txt = "\n".join(sample_movies)
        sample_json = json.dumps(sample_movies, indent=2)
        
        st.download_button(
            "📥 Download Sample CSV",
            sample_csv,
            "sample_movies.csv",
            "text/csv",
            use_container_width=True
        )
        
        st.download_button(
            "📥 Download Sample TXT",
            sample_txt,
            "sample_movies.txt",
            "text/plain",
            use_container_width=True
        )
        
        st.download_button(
            "📥 Download Sample JSON",
            sample_json,
            "sample_movies.json",
            "application/json",
            use_container_width=True
        )

def render_sidebar():
    """Render the sidebar with input options"""
    st.sidebar.title("🎬 Movie Input")
    
    # Single movie search in sidebar
    st.sidebar.subheader("🔍 Quick Search")
    quick_search = st.sidebar.text_input("Search single movie:", placeholder="Movie title...")
    if st.sidebar.button("Search", key="sidebar_search", use_container_width=True):
        st.session_state.quick_search_title = quick_search
    
    input_method = st.sidebar.radio(
        "Choose input method for batch processing:",
        ["Manual Input", "Upload File"]
    )
    
    movie_titles = []
    
    if input_method == "Manual Input":
        st.sidebar.subheader("✏️ Enter Movie Titles")
        movie_text = st.sidebar.text_area(
            "Enter movie titles (one per line):",
            height=200,
            placeholder="The Shawshank Redemption\nThe Godfather\nPulp Fiction\n...",
            help="Enter one movie title per line. Be as accurate as possible for better results."
        )
        if movie_text:
            movie_titles = [title.strip() for title in movie_text.split('\n') if title.strip()]
    
    else:  # File Upload
        st.sidebar.subheader("📁 Upload Movie List")
        uploaded_file = st.sidebar.file_uploader(
            "Choose a file",
            type=['txt', 'csv', 'json'],
            help="Supported formats: TXT, CSV, JSON"
        )
        
        if uploaded_file is not None:
            try:
                movie_titles = load_movies_from_file(uploaded_file)
                st.sidebar.success(f"✅ Loaded {len(movie_titles)} movies from {uploaded_file.name}")
            except Exception as e:
                st.sidebar.error(f"❌ Error reading file: {str(e)}")
    
    # API Status
    st.sidebar.subheader("🔑 API Status")
    st.sidebar.success("✅ OMDb API: Configured and Ready!")
    st.sidebar.info("Your API key is pre-configured and ready to use.")
    
    return movie_titles

def render_export_section(processed_movies):
    """Render export options"""
    st.subheader("📤 Export Results")
    
    if not processed_movies:
        st.info("No data to export")
        return
    
    # Convert to DataFrame for export
    data = []
    for movie in processed_movies:
        data.append({
            'Title': movie.get('title', ''),
            'Year': movie.get('year', 'Unknown'),
            'Genres': ', '.join(movie.get('genres', [])),
            'Rating': movie.get('rating', 'N/A'),
            'Votes': movie.get('votes', '0'),
            'Director': movie.get('director', 'Unknown'),
            'Actors': movie.get('actors', 'Unknown'),
            'Runtime': movie.get('runtime', 'Unknown'),
            'BoxOffice': movie.get('box_office', 'Unknown'),
            'Metascore': movie.get('metascore', 'N/A'),
            'Overview': movie.get('overview', ''),
            'Source': movie.get('source', 'Unknown')
        })
    
    df = pd.DataFrame(data)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = df.to_csv(index=False)
        st.download_button(
            "💾 Download CSV",
            csv_data,
            "classified_movies.csv",
            "text/csv",
            use_container_width=True,
            help="Export as CSV file for spreadsheets"
        )
    
    with col2:
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            "💾 Download JSON",
            json_data,
            "classified_movies.json",
            "application/json",
            use_container_width=True,
            help="Export as JSON file for developers"
        )
    
    with col3:
        # For Excel, we need to create a temporary file
        excel_file = "temp_movies.xlsx"
        df.to_excel(excel_file, index=False)
        with open(excel_file, "rb") as f:
            excel_data = f.read()
        st.download_button(
            "💾 Download Excel",
            excel_data,
            "classified_movies.xlsx",
            "application/vnd.ms-excel",
            use_container_width=True,
            help="Export as Excel file for business use"
        )
        # Clean up temporary file
        if os.path.exists(excel_file):
            os.remove(excel_file)

def render_rating_analysis(stats):
    """Render detailed rating analysis"""
    st.subheader("⭐ Rating Analysis")
    
    if not stats.get('rating_data'):
        st.info("No rating data available for analysis")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Rating distribution pie chart
        fig_pie = px.pie(
            values=list(stats['rating_categories'].values()),
            names=list(stats['rating_categories'].keys()),
            title="Rating Distribution",
            color=list(stats['rating_categories'].keys()),
            color_discrete_map={
                'Excellent (9-10)': '#00ff00',
                'Good (7-8.9)': '#aaff00', 
                'Average (5-6.9)': '#ffff00',
                'Poor (3-4.9)': '#ffaa00',
                'Bad (0-2.9)': '#ff0000'
            }
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Rating histogram
        fig_hist = px.histogram(
            x=stats['rating_data'],
            title="Rating Distribution Histogram",
            labels={'x': 'IMDb Rating', 'y': 'Number of Movies'},
            nbins=20,
            color_discrete_sequence=['#1f77b4']
        )
        fig_hist.update_layout(showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col3:
        # Rating statistics
        st.metric("Average Rating", f"{stats['average_rating']}/10")
        st.metric("Total Rated Movies", stats['total_ratings'])
        st.metric("Highest Rating", f"{max(stats['rating_data']):.1f}/10")
        st.metric("Lowest Rating", f"{min(stats['rating_data']):.1f}/10")
        
        # Rating categories breakdown
        st.write("**Rating Categories:**")
        for category, count in stats['rating_categories'].items():
            percentage = (count / stats['total_ratings']) * 100 if stats['total_ratings'] > 0 else 0
            st.write(f"{category}: {count} ({percentage:.1f}%)")

def render_top_rated_movies(stats):
    """Render top rated movies section"""
    if not stats.get('top_rated_movies'):
        return
    
    st.subheader("🏆 Top Rated Movies")
    
    for i, movie in enumerate(stats['top_rated_movies'], 1):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            rating = movie.get('rating')
            rating_class = get_rating_class(rating)
            st.write(f"**{i}. {movie.get('title')}** ({movie.get('year')})")
            st.markdown(f"<div class='{rating_class}'>⭐ {rating}/10 - {', '.join(movie.get('genres', []))}</div>", unsafe_allow_html=True)
            st.write(f"*{movie.get('overview')}*")
        
        with col2:
            poster_url = movie.get('poster', '')
            if poster_url and poster_url != 'N/A':
                st.image(poster_url, width=100)
        
        st.markdown("---")

def render_genre_tabs(classifier, classified_movies):
    """Render tabs for each genre"""
    st.subheader("🎭 Movies by Genre")
    
    # Create tabs for each genre that has movies
    genres_with_movies = [
        genre for genre in classifier.default_genres
        if (classified_movies and 
            len(classified_movies.get(genre, [])) > 0)
    ]
    
    if not genres_with_movies:
        st.info("No movies found in any genre categories.")
        return
    
    tabs = st.tabs([f"{genre} ({len(classified_movies[genre])})" for genre in genres_with_movies])
    
    for i, genre in enumerate(genres_with_movies):
        with tabs[i]:
            movies = classified_movies[genre]
            
            for movie in movies:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**🎬 {movie.get('title', 'Unknown')}** ({movie.get('year', 'Unknown')})")
                        
                        # Display rating with color coding
                        rating = movie.get('rating')
                        rating_class = get_rating_class(rating)
                        if rating and rating != 'N/A':
                            st.markdown(f"<div class='{rating_class}'>⭐ **{rating}/10**</div>", unsafe_allow_html=True)
                        
                        # Display additional movie info
                        if movie.get('director') and movie.get('director') != 'Unknown':
                            st.write(f"**Director:** {movie.get('director')}")
                        
                        if movie.get('actors') and movie.get('actors') != 'Unknown':
                            st.write(f"**Cast:** {movie.get('actors')}")
                        
                        if movie.get('overview') and movie.get('overview') != 'No information available':
                            st.write(f"**Plot:** {movie.get('overview')}")
                        
                    with col2:
                        if movie.get('runtime') and movie.get('runtime') != 'Unknown':
                            st.write(f"⏱️ {movie.get('runtime')}")
                        
                        source = movie.get('source', 'Unknown')
                        color = "🟢" if source != "Not Found" else "🔴"
                        st.write(f"{color} {source}")
                        
                        # Show poster if available
                        poster_url = movie.get('poster', '')
                        if poster_url and poster_url != 'N/A':
                            st.image(poster_url, width=100)
                    
                    st.markdown("---")

def render_results(classifier, classified_movies, processed_movies):
    """Render the classification results"""
    
    # Statistics
    stats = classifier.get_statistics()
    
    # Display statistics in columns
    st.subheader("📊 Classification Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Movies", stats['total_movies'])
    with col2:
        st.metric("Movies Found", stats['found_movies'])
    with col3:
        st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
    with col4:
        st.metric("Avg Rating", f"{stats['average_rating']:.1f}/10" if stats['average_rating'] else "N/A")
    
    # Additional stats
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Not Found", stats['not_found_movies'])
    with col2:
        st.metric("Rated Movies", stats['total_ratings'])
    
    # Genre distribution chart
    if stats['genre_counts']:
        st.subheader("📈 Genre Distribution")
        fig = px.bar(
            x=list(stats['genre_counts'].keys()),
            y=list(stats['genre_counts'].values()),
            title="Number of Movies by Genre",
            labels={'x': 'Genre', 'y': 'Number of Movies'},
            color=list(stats['genre_counts'].values()),
            color_continuous_scale='blues'
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    # Rating analysis
    render_rating_analysis(stats)
    
    # Top rated movies
    render_top_rated_movies(stats)
    
    # Export options
    render_export_section(processed_movies)
    
    # Genre tabs
    render_genre_tabs(classifier, classified_movies)

def main():
    """Main application function"""
    st.markdown('<h1 class="main-header">🎬 Automated Movie Genre Classification System</h1>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'classified_movies' not in st.session_state:
        st.session_state.classified_movies = None
    if 'processed_movies' not in st.session_state:
        st.session_state.processed_movies = None
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'classifier' not in st.session_state:
        st.session_state.classifier = MovieGenreClassifier()
    if 'quick_search_title' not in st.session_state:
        st.session_state.quick_search_title = None
    
    classifier = st.session_state.classifier
    
    # Handle quick search from sidebar
    if st.session_state.quick_search_title:
        render_single_movie_search(classifier)
        # Clear the search after displaying
        st.session_state.quick_search_title = None
    else:
        # Show single movie search at the top
        render_single_movie_search(classifier)
    
    # Get movie titles from sidebar for batch processing
    movie_titles = render_sidebar()
    
    if not movie_titles and not st.session_state.quick_search_title:
        # render_welcome_screen()
        return
    
    if not movie_titles:
        return
    
    # Validate titles
    valid_titles, invalid_titles = validate_movie_titles(movie_titles)
    
    if invalid_titles:
        st.warning(f"Found {len(invalid_titles)} invalid titles that will be skipped.")
        with st.expander("Show invalid titles"):
            for title in invalid_titles:
                st.write(f"❌ {title}")
    
    if not valid_titles:
        st.error("❌ No valid movie titles to process.")
        return
    
    st.success(f"✅ Ready to process {len(valid_titles)} valid movie titles!")
    
    # Process movies button
    if st.button("🚀 Classify Movies", type="primary", use_container_width=True):
        with st.spinner("🔄 Classifying movies using OMDb API..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(current, total):
                progress = current / total
                progress_bar.progress(progress)
                status_text.text(f"🔍 Processing {current}/{total} movies...")
            
            # Classify movies
            classified_movies = classifier.classify_movies(
                valid_titles, 
                progress_callback=update_progress
            )
            
            # Update session state
            st.session_state.classified_movies = classified_movies
            st.session_state.processed_movies = classifier.processed_movies
            st.session_state.processing_complete = True
            
            progress_bar.progress(1.0)
            status_text.text("✅ Classification complete!")
            time.sleep(0.5)
            st.balloons()
    
    # Show results if processing is complete
    if st.session_state.processing_complete:
        render_results(
            classifier, 
            st.session_state.classified_movies, 
            st.session_state.processed_movies
        )

if __name__ == "__main__":
    main()