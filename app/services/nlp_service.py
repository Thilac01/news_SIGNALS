"""
NLP Service for Location Extraction from News Articles
Extracts location entities from processed news content (all sources) using spaCy NLP
"""

import pandas as pd
import spacy
from collections import Counter
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Expanded Sri Lankan location coordinates
SRI_LANKA_LOCATIONS = {
    "Colombo": {"lat": 6.9271, "lon": 79.8612, "count": 0},
    "Kandy": {"lat": 7.2906, "lon": 80.6337, "count": 0},
    "Galle": {"lat": 6.0535, "lon": 80.2210, "count": 0},
    "Jaffna": {"lat": 9.6615, "lon": 80.0255, "count": 0},
    "Trincomalee": {"lat": 8.5874, "lon": 81.2152, "count": 0},
    "Anuradhapura": {"lat": 8.3114, "lon": 80.4037, "count": 0},
    "Matara": {"lat": 5.9549, "lon": 80.5550, "count": 0},
    "Negombo": {"lat": 7.2008, "lon": 79.8358, "count": 0},
    "Kurunegala": {"lat": 7.4863, "lon": 80.3623, "count": 0},
    "Hambantota": {"lat": 6.1429, "lon": 81.1212, "count": 0},
    "Batticaloa": {"lat": 7.7310, "lon": 81.6747, "count": 0},
    "Ratnapura": {"lat": 6.7056, "lon": 80.3847, "count": 0},
    "Nuwara Eliya": {"lat": 6.9497, "lon": 80.7891, "count": 0},
    "Badulla": {"lat": 6.9934, "lon": 81.0550, "count": 0},
    "Kegalle": {"lat": 7.2513, "lon": 80.3464, "count": 0},
    "Matale": {"lat": 7.4675, "lon": 80.6234, "count": 0},
    "Gampaha": {"lat": 7.0840, "lon": 79.9990, "count": 0},
    "Kalutara": {"lat": 6.5854, "lon": 79.9607, "count": 0},
    "Monaragala": {"lat": 6.8728, "lon": 81.3507, "count": 0},
    "Puttalam": {"lat": 8.0362, "lon": 79.8283, "count": 0},
    "Vavuniya": {"lat": 8.7542, "lon": 80.4982, "count": 0},
    "Mannar": {"lat": 8.9810, "lon": 79.9044, "count": 0},
    "Ampara": {"lat": 7.2974, "lon": 81.6722, "count": 0},
    "Polonnaruwa": {"lat": 7.9403, "lon": 81.0188, "count": 0},
    "Kilinochchi": {"lat": 9.3961, "lon": 80.3990, "count": 0},
    "Mullaitivu": {"lat": 9.2671, "lon": 80.8142, "count": 0},
    "Dambulla": {"lat": 7.8731, "lon": 80.6511, "count": 0},
    "Sigiriya": {"lat": 7.9570, "lon": 80.7603, "count": 0},
    "Bentota": {"lat": 6.4218, "lon": 79.9975, "count": 0},
    "Hikkaduwa": {"lat": 6.1395, "lon": 80.1000, "count": 0},
    "Unawatuna": {"lat": 6.0123, "lon": 80.2470, "count": 0},
    "Ella": {"lat": 6.8667, "lon": 81.0466, "count": 0},
    "Kataragama": {"lat": 6.4135, "lon": 81.3325, "count": 0},
    "Tissamaharama": {"lat": 6.2737, "lon": 81.2872, "count": 0},
    "Embilipitiya": {"lat": 6.3364, "lon": 80.8523, "count": 0},
    "Chilaw": {"lat": 7.5758, "lon": 79.8601, "count": 0},
    "Dehiwala": {"lat": 6.8511, "lon": 79.8659, "count": 0},
    "Moratuwa": {"lat": 6.7730, "lon": 79.8816, "count": 0},
    "Kotte": {"lat": 6.8970, "lon": 79.9048, "count": 0},
    "Tangalle": {"lat": 6.0240, "lon": 80.7946, "count": 0},
    "Mirissa": {"lat": 5.9482, "lon": 80.4716, "count": 0},
}

DATA_FILE = os.path.join("data", "final_data.csv")

# Global NLP model instance
nlp_model = None


def load_nlp_model():
    """Load spaCy NLP model (singleton pattern)"""
    global nlp_model
    if nlp_model is None:
        try:
            nlp_model = spacy.load("en_core_web_sm")
            logger.info("spaCy model loaded successfully")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
            raise
    return nlp_model


def extract_locations_from_text(text):
    """
    Extract location entities from text using spaCy NLP
    
    Args:
        text: Text content to analyze
        
    Returns:
        List of location names
    """
    if not isinstance(text, str):
        return []
        
    nlp = load_nlp_model()
    doc = nlp(text)
    
    locations = []
    for ent in doc.ents:
        # GPE: Geopolitical entities (countries, cities, states)
        # LOC: Non-GPE locations (mountain ranges, bodies of water)
        # FAC: Facilities (buildings, airports, highways, bridges)
        if ent.label_ in ["GPE", "LOC", "FAC"]:
            locations.append(ent.text)
    
    return locations


def get_location_data():
    """
    Fetch news articles from CSV and extract location frequency data
    
    Returns:
        Dictionary with location data including coordinates, counts, and related news
    """
    # Reset counts and news list
    location_data = {loc: {"lat": data["lat"], "lon": data["lon"], "count": 0, "news": []} 
                     for loc, data in SRI_LANKA_LOCATIONS.items()}
    
    if not os.path.exists(DATA_FILE):
        logger.warning(f"Data file {DATA_FILE} not found.")
        return location_data
        
    try:
        df = pd.read_csv(DATA_FILE)
        logger.info(f"Loaded {len(df)} articles for location analysis")
    except Exception as e:
        logger.error(f"Error reading data file: {e}")
        return location_data
    
    # Process each article (Title + Summary)
    processed = 0
    for _, row in df.iterrows():
        try:
            text = str(row.get('Title', '')) + " " + str(row.get('Summary', ''))
            article_info = {
                "Title": row.get('Title'),
                "Link": row.get('Link'),
                "Source": row.get('Source'),
                "Summary": row.get('Summary'),
                "Date": row.get('Date')
            }
            
            # Extract locations from this article
            extracted_locations = extract_locations_from_text(text)
            
            # Find generic matches for this article
            # We use a set to avoid adding the same article multiple times to the same location 
            # (even if the location is mentioned multiple times in the text)
            matched_locations_in_article = set()
            
            for extracted_loc in extracted_locations:
                extracted_lower = extracted_loc.lower()
                
                for known_loc in SRI_LANKA_LOCATIONS.keys():
                    known_lower = known_loc.lower()
                    
                    # Check for match (Exact or Substring)
                    if known_lower == extracted_lower or \
                       (known_lower in extracted_lower and len(extracted_lower) < len(known_lower) + 15):
                        matched_locations_in_article.add(known_loc)
            
            # Update the global data with matches from this article
            for loc in matched_locations_in_article:
                location_data[loc]["count"] += 1
                location_data[loc]["news"].append(article_info)
            
            processed += 1
            
        except Exception as e:
            logger.debug(f"Error processing row: {e}")
            continue
    
    logger.info(f"Processed {processed} articles for locations")

    # Filter out locations with zero counts for cleaner data
    filtered_data = {loc: data for loc, data in location_data.items() if data["count"] > 0}
    
    logger.info(f"Found {len(filtered_data)} Sri Lankan locations with mentions")
    return filtered_data


def get_heatmap_data():
    """
    Get location data formatted for heatmap visualization
    
    Returns:
        List of [lat, lon, intensity] arrays for heatmap
    """
    location_data = get_location_data()
    
    # Convert to heatmap format: [lat, lon, intensity]
    heatmap_points = []
    for loc, data in location_data.items():
        if data["count"] > 0:
            heatmap_points.append([data["lat"], data["lon"], data["count"]])
    
    return heatmap_points


def get_location_summary():
    """
    Get a summary of top locations mentioned in news
    
    Returns:
        Dictionary with location statistics
    """
    location_data = get_location_data()
    
    # Sort by count
    sorted_locations = sorted(
        [(loc, data) for loc, data in location_data.items()],
        key=lambda x: x[1]["count"],
        reverse=True
    )
    
    return {
        "total_locations": len(location_data),
        "top_locations": [
            {
                "name": loc,
                "count": data["count"],
                "lat": data["lat"],
                "lon": data["lon"]
            }
            for loc, data in sorted_locations[:10]
        ],
        "all_locations": location_data
    }
