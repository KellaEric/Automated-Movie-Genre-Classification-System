import streamlit as st
import pandas as pd
import time
import os
from movie_classifier import MovieGenreClassifier
from utils import load_movies_from_file, export_to_csv, export_to_json, validate_movie_titles
from config import DEFAULT_GENRES
import plotly.express as px
import plotly.graph_objects as go

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
</style>
""", unsafe_allow_html=True)

class MovieClassifierApp:
    def __init__(self):
        self.classifier = MovieGenreClassifier()
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'classified_movies' not in st.session_state:
            st.session_state.classified_movies = None
        if 'processed_movies' not in st.session_state:
            st.session_state.processed_movies = None
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
    
    def render_sidebar(self):
        """Render the sidebar with input options"""
        st.sidebar.title("🎬 Movie Input")
        
        input_method = st.sidebar.radio(
            "Choose input method:",
            ["Manual Input", "Upload File"]
        )
        
        movie_titles = []
        
        if input_method == "Manual Input":
            st.sidebar.subheader("Enter Movie Titles")
            movie_text = st.sidebar.text_area(
                "Enter movie titles (one per line):",
                height=200,
                placeholder="The Shawshank Redemption\nThe Godfather\nPulp Fiction\n..."
            )
            if movie_text:
                movie_titles = [title.strip() for title in movie_text.split('\n') if title.strip()]
        
        else:  # File Upload
            st.sidebar.subheader("Upload Movie List")
            uploaded_file = st.sidebar.file_uploader(
                "Choose a file",
                type=['txt', 'csv', 'json'],
                help="Supported formats: TXT, CSV, JSON"
            )
            
            if uploaded_file is not None:
                # Save uploaded file temporarily
                with open("temp_uploaded_file", "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                try:
                    movie_titles = load_movies_from_file("temp_uploaded_file")
                    st.sidebar.success(f"Loaded {len(movie_titles)} movies from {uploaded_file.name}")
                except Exception as e:
                    st.sidebar.error(f"Error reading file: {str(e)}")
                finally:
                    # Clean up temporary file
                    if os.path.exists("temp_uploaded_file"):
                        os.remove("temp_uploaded_file")
        
        # API Configuration
        st.sidebar.subheader("🔧 Configuration")
        st.sidebar.info(
            "For best results, add your API keys in config.py:\n"

            "- OMDb API: http://www.omdbapi.com/apikey.aspx"
        )
        
        return movie_titles
    
    def render_main_content(self):
        """Render the main content area"""
        st.markdown('<h1 class="main-header">🎬 Automated Movie Genre Classification System</h1>', unsafe_allow_html=True)
        
        # Get movie titles from sidebar
        movie_titles = self.render_sidebar()
        
        if not movie_titles:
            self.render_welcome_screen()
            return
        
        # Validate titles
        valid_titles, invalid_titles = validate_movie_titles(movie_titles)
        
        if invalid_titles:
            st.warning(f"Found {len(invalid_titles)} invalid titles that will be skipped.")
            with st.expander("Show invalid titles"):
                st.write(invalid_titles)
        
        if not valid_titles:
            st.error("No valid movie titles to process.")
            return
        
        # Process movies
        if st.button("🚀 Classify Movies", type="primary", use_container_width=True):
            self.process_movies(valid_titles)
        
        # Show results if processing is complete
        if st.session_state.processing_complete:
            self.render_results()
    
    def render_welcome_screen(self):
        """Render welcome screen with instructions"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Welcome to the Movie Genre Classifier!")
            st.markdown("""
            This system automatically classifies movies into genres using information from movie databases.
            
            ### How to use:
            1. **Enter movie titles** manually in the sidebar OR **upload a file** (TXT, CSV, or JSON)
            2. Click the **"Classify Movies"** button
            3. View the results organized by genre
            4. Export your classified movie list
            
            ### Supported Input Formats:
            - **TXT file**: One movie title per line
            - **CSV file**: Movie titles in the first column
            - **JSON file**: Array of movie titles or object with 'movies' key
            
            ### Features:
            ✅ Automatic genre classification  
            ✅ Movie metadata extraction  
            ✅ Statistical analysis  
            ✅ Multiple export formats  
            ✅ Progress tracking  
            """)
        
        with col2:
            st.subheader("Sample Data")
            sample_movies = [
                "The Shawshank Redemption",
                "The Godfather",
                "The Dark Knight",
                "Pulp Fiction",
                "Forrest Gump",
                "Inception",
                "The Matrix",
                "Goodfellas"
            ]
            
            # Create sample files
            sample_csv = "\n".join([f"Movie Title\n{movie}" for movie in sample_movies])
            sample_txt = "\n".join(sample_movies)
            # sample_json = st.json.dumps(sample_movies, indent=2)
            
            st.download_button(
                "Download Sample CSV",
                sample_csv,
                "sample_movies.csv",
                "text/csv"
            )
            
            st.download_button(
                "Download Sample TXT",
                sample_txt,
                "sample_movies.txt",
                "text/plain"
            )
            
            st.download_button(
                "Download Sample JSON",
                # sample_json,
                "sample_movies.json",
                "application/json"
            )
    
    def process_movies(self, movie_titles: list):
        """Process the movie titles and classify them"""
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"Processing {current}/{total} movies...")
        
        # Classify movies
        with st.spinner("Classifying movies..."):
            classified_movies = self.classifier.classify_movies(
                movie_titles, 
                progress_callback=update_progress
            )
        
        # Update session state
        st.session_state.classified_movies = classified_movies
        st.session_state.processed_movies = self.classifier.processed_movies
        st.session_state.processing_complete = True
        
        progress_bar.progress(1.0)
        status_text.text("Classification complete!")
        time.sleep(0.5)
        st.success("🎉 Movie classification completed successfully!")
    
    def render_results(self):
        """Render the classification results"""
        if not st.session_state.processing_complete:
            return
        
        # Statistics
        stats = self.classifier.get_statistics()
        
        # Display statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Movies", stats['total_movies'])
        with col2:
            st.metric("Movies Found", stats['found_movies'])
        with col3:
            st.metric("Success Rate", f"{stats['success_rate']:.1f}%")
        with col4:
            st.metric("Unique Genres", len(stats['genre_counts']))
        
        # Genre distribution chart
        if stats['genre_counts']:
            fig = px.bar(
                x=list(stats['genre_counts'].keys()),
                y=list(stats['genre_counts'].values()),
                title="Genre Distribution",
                labels={'x': 'Genre', 'y': 'Number of Movies'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Export options
        self.render_export_section()
        
        # Genre tabs
        self.render_genre_tabs()
    
    def render_export_section(self):
        """Render export options"""
        st.subheader("📤 Export Results")
        
        col1, col2, col3 = st.columns(3)
        
        # Convert to DataFrame for export
        df = self.classifier.export_to_dataframe()
        
        with col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "Download CSV",
                csv_data,
                "classified_movies.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col2:
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                "Download JSON",
                json_data,
                "classified_movies.json",
                "application/json",
                use_container_width=True
            )
        
        with col3:
            excel_data = df.to_excel("temp_movies.xlsx", index=False)
            with open("temp_movies.xlsx", "rb") as f:
                st.download_button(
                    "Download Excel",
                    f.read(),
                    "classified_movies.xlsx",
                    "application/vnd.ms-excel",
                    use_container_width=True
                )
            # Clean up temporary file
            if os.path.exists("temp_movies.xlsx"):
                os.remove("temp_movies.xlsx")
    
    def render_genre_tabs(self):
        """Render tabs for each genre"""
        st.subheader("🎭 Movies by Genre")
        
        # Create tabs for each genre that has movies
        genres_with_movies = [
            genre for genre in DEFAULT_GENRES + ['Unknown'] 
            if (st.session_state.classified_movies and 
                len(st.session_state.classified_movies.get(genre, [])) > 0)
        ]
        
        if not genres_with_movies:
            st.info("No movies found in any genre categories.")
            return
        
        tabs = st.tabs([f"{genre} ({len(st.session_state.classified_movies[genre])})" for genre in genres_with_movies])
        
        for i, genre in enumerate(genres_with_movies):
            with tabs[i]:
                movies = st.session_state.classified_movies[genre]
                
                for movie in movies:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.write(f"**{movie.get('title', 'Unknown')}** ({movie.get('year', 'Unknown')})")
                            if movie.get('overview'):
                                st.write(movie.get('overview'))
                        
                        with col2:
                            rating = movie.get('rating')
                            if rating and rating != 'N/A':
                                st.write(f"⭐ Rating: {rating}/10")
                            st.write(f"Source: {movie.get('source', 'Unknown')}")
                        
                        st.markdown("---")

def main():
    app = MovieClassifierApp()
    app.render_main_content()

if __name__ == "__main__":
    main()