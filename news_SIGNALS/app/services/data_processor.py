import feedparser
import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants and Configuration
SEO_PRIORITY = {
    "Ada Derana": 5.17, "Daily Mirror": 7.47, "Lankadeepa": 6.78, "The Island": 6.38,
    "Divaina": 6.65, "Thinakaran": 5.5, "Sunday Times": 5.95, "Dinamina": 5.9,
    "Virakesari": 5.72, "Daily News": 5.8, "Silumina": 5.58, "EconomyNext": 6.65,
    "FT.LK": 6.58, "LankaBusinessOnline": 6.92, "News.lk": 6.4, "Ceylon Today": 5.75,
    "ITN News": 7.42, "Onlanka.com": 6.45
}

RSS_FEEDS = {
    "Ada Derana": "https://www.adaderana.lk/rss.php",
    "Daily Mirror": "https://www.dailymirror.lk/rss.xml",
    "The Island": "https://island.lk/feed/",
    "Sunday Times": "https://www.sundaytimes.lk/rss.xml",
    "Ceylon Today": "https://www.ceylontoday.lk/rss",
    "Daily News": "https://www.dailynews.lk/feed",
    "FT.LK": "https://www.ft.lk/rss",
    "EconomyNext": "https://www.economynext.com/feed",
    "News.lk": "https://news.lk/news?format=feed",
    "Onlanka.com": "https://www.onlanka.com/feed",
    "LankaBusinessOnline": "https://www.lankabusinessonline.com/feed",
    "ITN News": "https://www.itnnews.lk/feed",
    "Lankadeepa": "https://www.lankadeepa.lk/rss",
    "Divaina": "https://www.divaina.com/rss",
    "Dinamina": "https://www.dinamina.lk/rss",
    "Silumina": "https://www.silumina.lk/rss",
    "Thinakaran": "https://www.thinakaran.lk/rss",
    "Virakesari": "https://www.virakesari.lk/rss"
}

LEXICON = {
    # NEGATIVE (RISK)
    "disaster": -3,
    "flood": -3,
    "cyclone": -3,
    "earthquake": -3,
    "landslide": -3,
    "crisis": -3,
    "evacuation": -3,
    "fire": -3,
    "storm": -3,
    "tornado": -3,
    "hazard": -3,
    "accident": -3,
    "casualty": -3,
    "fatality": -3,
    "collapse": -3,
    "chaos": -3,
    "riot": -3,
    "civil_unrest": -3,
    "structural_failure": -3,
    "danger": -3,
    "displaced": -3,
    "pandemic": -3,
    "epidemic": -3,
    "disease_outbreak": -3,
    "dies": -3,
    "died": -3,
    "death": -3,
    "dead": -3,
    "drought": -3,
    "tsunami": -3,
    "mudslide": -3,
    "wildfire": -3,
    "monsoon_damage": -3,
    
    # Health & Safety Risks
    "quarantine": -2,
    "health_alert": -2,
    "infection": -2,
    "infection_rate": -2,
    "dengue": -2,
    "malaria": -2,
    "cholera": -2,
    "contamination": -2,
    "poisoning": -2,
    "outbreak": -2,
    "virus": -2,
    "contagious": -2,
    "hospital_overcrowding": -2,
    "medical_emergency": -2,
    
    # Infrastructure & Utilities
    "outage": -2,
    "power_cut": -2,
    "power_outage": -2,
    "blackout": -2,
    "water_shortage": -2,
    "water_cut": -2,
    "fuel_shortage": -2,
    "gas_shortage": -2,
    "supply_disruption": -2,
    "service_interruption": -2,
    "breakdown": -2,
    "malfunction": -2,
    "infrastructure_damage": -2,
    
    # Transport & Traffic
    "transport_strike": -2,
    "road_accident": -2,
    "traffic_disruption": -2,
    "congestion": -1,
    "traffic_jam": -1,
    "road_closure": -2,
    "train_delay": -1,
    "bus_strike": -2,
    "airport_closure": -2,
    "flight_cancellation": -1,
    "port_closure": -2,
    
    # Economic Risks
    "inflation": -2,
    "loss": -2,
    "recession": -3,
    "economic_crash": -3,
    "inflation_spike": -3,
    "currency_devaluation": -3,
    "bankruptcy": -3,
    "debt_crisis": -3,
    "default": -3,
    "financial_crisis": -3,
    "market_crash": -3,
    "unemployment": -2,
    "layoff": -2,
    "job_loss": -2,
    "poverty": -2,
    "economic_decline": -2,
    "budget_deficit": -2,
    "tax_increase": -2,
    "price_hike": -2,
    "cost_increase": -2,
    
    # Tourism & Business
    "tourism_decline": -2,
    "business_closure": -2,
    "factory_shutdown": -2,
    "production_halt": -2,
    "export_decline": -2,
    "revenue_drop": -2,
    "profit_decline": -2,
    
    # Environmental
    "pollution": -2,
    "air_quality": -2,
    "climate_change": -1,
    "deforestation": -2,
    "environmental_damage": -2,
    "toxic": -2,
    "waste_crisis": -2,
    
    # Security & Crime
    "attack": -3,
    "crime": -2,
    "arrest": -2,
    "terror": -3,
    "terrorism": -3,
    "violence": -3,
    "conflict": -3,
    "robbery": -2,
    "burglary": -2,
    "assault": -2,
    "kidnap": -3,
    "hijack": -3,
    "illegal_activity": -2,
    "law_violation": -2,
    "threat": -2,
    "murder": -3,
    "shooting": -3,
    "bombing": -3,
    "explosion": -3,
    "sabotage": -2,
    "vandalism": -2,
    "theft": -2,
    "fraud": -2,
    "corruption": -2,
    "bribery": -2,
    
    # Political & Social Unrest
    "protest": -2,
    "demonstration": -1,
    "strike": -2,
    "boycott": -2,
    "political_crisis": -3,
    "government_collapse": -3,
    "resignation": -2,
    "impeachment": -2,
    "scandal": -2,
    "controversy": -1,
    "dispute": -1,
    "tension": -1,
    
    # Location-Specific Risks (Sri Lankan cities)
    "colombo_flood": -3,
    "kandy_protest": -2,
    "galle_traffic": -1,
    "negombo_storm": -2,
    "anuradhapura_drought": -2,
    "panadura_flood": -3,
    "kurunegala_traffic": -1,
    "matara_flood": -3,
    "colombo_protest": -2,
    "galle_bridge_collapse": -3,
    "colombo_airport_delay": -2,
    "jaffna_unrest": -2,
    "trincomalee_conflict": -2,
    
    # Risk Indicators
    "risk_alert": -1,
    "warning": -1,
    "emergency": -2,
    "urgent": -1,
    "critical": -2,
    "severe": -2,
    "serious": -1,
    "concern": -1,
    "issue": -1,
    "problem": -1,
    "failure": -2,
    "damage": -2,
    "destruction": -3,
    "devastation": -3,

    # POSITIVE (OPPORTUNITY) - Aid & Relief
    "donation": 2,
    "aid": 3,
    "restoration": 3,
    "restore":3,
    "relief": 2,
    "funding": 2,
    "charity": 2,
    "assistance": 2,
    "grant": 2,
    "shelter": 2,
    "medical_support": 2,
    "support": 2,
    "rescue_team": 2,
    "volunteer": 2,
    "food_distribution": 2,
    "emergency_fund": 2,
    "rebuilding": 2,
    "recovery": 3,
    "rehabilitation": 2,
    "community_help": 2,
    "ngo_project": 2,
    "humanitarian_aid": 2,
    "disaster_relief": 2,
    
    # Economic Opportunities
    "investment": 2,
    "trade": 2,
    "profit": 2,
    "revenue": 2,
    "export": 2,
    "business_growth": 2,
    "economic_upturn": 2,
    "economic_growth": 2,
    "startup": 2,
    "entrepreneurship": 2,
    "capital": 2,
    "business_expansion": 2,
    "project_funding": 2,
    "contract_award": 2,
    "economic_forecast": 1,
    "profit_max": 3,
    "booming": 3,
    "resilient_economy": 3,
    "gdp_growth": 2,
    "foreign_exchange": 2,
    "remittance": 2,
    "revenue_increase": 3,
    "profit_record": 3,
    "market_expansion": 2,
    "business_partnership": 2,
    "job_creation": 2,
    "employment": 2,
    "salary_increase": 2,
    "wage_growth": 2,
    
    # Industry & Trade (Sri Lankan context)
    "tea_export": 2,
    "garment_industry": 2,
    "tourism_growth": 2,
    "foreign_investment": 2,
    "industrial_development": 2,
    "ratnapura_tea_export": 2,
    "tea_export_success": 2,
    "garment_factory_opening": 2,
    "tourism_peak": 2,
    "foreign_aid_received": 2,
    "infrastructure_grant": 2,
    "startup_funding": 2,
    "spice_export": 2,
    "coconut_export": 2,
    "rubber_export": 2,
    "fisheries_growth": 2,
    "agriculture_development": 2,
    "manufacturing_growth": 2,
    "it_sector_growth": 2,
    "technology_investment": 2,
    
    # Infrastructure & Development
    "infrastructure_development": 2,
    "infrastructure_upgrade": 2,
    "project_completion": 2,
    "energy_supply": 2,
    "utility_service": 1,
    "road_construction": 2,
    "highway_opening": 2,
    "bridge_construction": 2,
    "port_development": 2,
    "airport_expansion": 2,
    "railway_modernization": 2,
    "power_plant": 2,
    "renewable_energy": 2,
    "solar_project": 2,
    "wind_energy": 2,
    "hydropower": 2,
    
    # Health & Medical
    "disease_control": 2,
    "healthcare_improvement": 2,
    "medical_facility_upgrade": 2,
    "hospital_expansion": 2,
    "vaccination_campaign": 2,
    "health_program": 2,
    "medical_breakthrough": 2,
    "treatment_success": 2,
    
    # Social & Community
    "conservation": 2,
    "reforestation": 2,
    "sustainable_development": 2,
    "social_initiative": 2,
    "youth_program": 2,
    "community_project": 2,
    "awareness_campaign": 1,
    "gender_equality": 2,
    "poverty_alleviation": 2,
    "cultural_event": 1,
    "heritage": 1,
    "volunteering": 2,
    "public_participation": 2,
    "environmental_protection": 2,
    "education_program": 2,
    "scholarship": 2,
    "skill_development": 2,
    "training_program": 2,
    
    # Governance & Policy
    "flexibility": 2,
    "initiative": 1,
    "announcement": 1,
    "resolution": 1,
    "strategy": 1,
    "policy_update": 1,
    "regulatory_change": 1,
    "government_order": 1,
    "reform": 2,
    "legislation": 1,
    "approval": 1,
    "agreement": 2,
    "treaty": 2,
    "partnership": 2,
    "collaboration": 2,
    "cooperation": 2,
    "permission": 3,
    "granted":2,
    # Security & Safety
    "patrol": 1,
    "public_safety": 1,
    "security_enhancement": 2,
    "peacekeeping": 2,
    "stability": 2,
    "law_enforcement": 1,
    
    # Positive Indicators
    "success": 2,
    "achievement": 2,
    "progress": 2,
    "improvement": 2,
    "advancement": 2,
    "innovation": 2,
    "breakthrough": 2,
    "milestone": 2,
    "victory": 2,
    "win": 2,
    "award": 2,
    "recognition": 2,
    "excellence": 2,
    "quality": 1,
    "efficiency": 1,
    "productivity": 2,
    "performance": 1,
    "growth": 2,
    "expansion": 2,
    "development": 2,
    "upgrade": 2,
    "modernization": 2,
    "transformation": 2,
    "provide":2,
    "launched":3,
}

OPERATIONAL_KEYWORDS = {
    "weather": [
        "flood", "storm", "cyclone", "landslide", "rain", "drought", "monsoon", 
        "weather", "forecast", "climate", "reservoir", "dam", "water level", 
        "irrigation", "rainfall", "atmospheric", "meteorological", "temperature", 
        "heat", "wind", "warning", "alert", "disaster", "natural hazard", 
        "tsunami", "earthquake", "humidity", "precipitation"
    ],
    "transport": [
        "traffic", "accident", "train", "bus", "highway", "road", "railway", 
        "airport", "flight", "transport", "vehicle", "locomotive", "station", 
        "port", "shipping", "cargo", "freight", "airline", "aviation", "driver", 
        "passenger", "commute", "expressway", "bridge", "tunnel", "logistics", 
        "fleet", "transit", "ticket", "departure", "arrival", "collision"
    ],
    "energy": [
        "outage", "power", "water cut", "fuel", "gas", "electricity", "energy", 
        "oil", "petrol", "diesel", "utility", "grid", "ceb", "cpc", "renewable", 
        "solar", "wind power", "hydro", "coal", "plant", "refinery", "cylinder", 
        "shortage", "tariff", "bill", "generation", "breakdown", "maintenance", 
        "supply", "kerosene", "litro", "laugfs", "station"
    ],
    "health": [
        "disease", "infection", "hospital", "medical", "health", "virus", 
        "pandemic", "dengue", "medicine", "doctor", "nurse", "clinic", "patient", 
        "treatment", "drug", "pharmaceutical", "vaccine", "surgery", "emergency", 
        "ambulance", "ministry of health", "nutrition", "wellness", "mental health", 
        "sanitation", "hygiene", "epidemic", "fever", "cancer", "diabetes"
    ],
    "security": [
        "crime", "arrest", "violence", "attack", "police", "military", "security", 
        "defense", "navy", "army", "court", "legal", "law", "enforcement", 
        "custody", "prison", "jail", "suspect", "investigation", "cid", "air force", 
        "troops", "border", "smuggling", "illegal", "operation", "weapon", "drug bust",
        "narcotics", "terrorism", "intelligence", "officer"
    ],
    "economic": [
        "inflation", "investment", "trade", "market", "stock", "currency", 
        "rupee", "bank", "interest rate", "economy", "finance", "tax", "budget", 
        "gdp", "cpi", "colombo stock exchange", "cse", "shares", "bond", "treasury", 
        "debt", "loan", "imf", "world bank", "central bank", "cbsl", "export", 
        "import", "customs", "tariff", "duty", "salary", "wage", "price", "cost", 
        "business", "industry", "profit", "loss", "funding"
    ],
    "sentiment": [
        "protest", "public opinion", "social media", "trend", "viral", "sentiment", 
        "outcry", "campaign", "boycott", "strike", "demonstration",
        "poll", "survey", "election", "vote", "voter", "community", "social", 
        "society", "civil", "rights", "activist", "union", "opposition", 
        "demand", "petition", "complaint", "feedback", "review", "comment", 
        "discussion", "debate", "speech", "rally", "march", "gathering",
        "movement", "public", "people", "citizens", "population",
        "government", "president", "minister", "parliament", "policy",
        "issue", "concern", "crisis", "develop", "situation", "matter"
    ]
}

# Normalize lexicon
NORM_LEX = {k.replace("_", " "): v for k, v in LEXICON.items()}


# Initial setup for NLTK
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download("vader_lexicon")

STOP_WORDS = set(stopwords.words("english"))
SIA = SentimentIntensityAnalyzer()

# Global model variable
MODEL = None
CURRENT_MODEL_NAME = "all-MiniLM-L6-v2"
MODEL_STATUS = "Not Loaded"

AVAILABLE_MODELS = [
    "all-MiniLM-L6-v2",
    "all-mpnet-base-v2",
    "paraphrase-multilingual-MiniLM-L12-v2",
    "multi-qa-MiniLM-L6-cos-v1",
    "distiluse-base-multilingual-cased-v1"
]

def get_current_model_info():
    return {
        "current_model": CURRENT_MODEL_NAME,
        "status": MODEL_STATUS,
        "available_models": AVAILABLE_MODELS
    }

def load_model_background(model_name):
    global MODEL, MODEL_STATUS, CURRENT_MODEL_NAME
    logger.info(f"Starting to load model: {model_name}")
    MODEL_STATUS = "Loading..."
    try:
        device = "cpu"
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
        except ImportError:
            pass
        
        # Load the model
        new_model = SentenceTransformer(model_name, device=device)
        
        # Update globals only after successful load
        MODEL = new_model
        CURRENT_MODEL_NAME = model_name
        MODEL_STATUS = "Ready"
        logger.info(f"Model {model_name} loaded successfully.")
    except Exception as e:
        logger.error(f"Error loading model {model_name}: {e}")
        MODEL_STATUS = f"Error: {str(e)}"

def switch_model(model_name):
    global MODEL_STATUS
    if model_name not in AVAILABLE_MODELS:
        # Allow custom models if user types them, but for now stick to list or allow passing any string
        # Let's allow any string but warn
        pass
    
    if MODEL_STATUS == "Loading...":
        return False, "A model is already loading."

    import threading
    thread = threading.Thread(target=load_model_background, args=(model_name,))
    thread.start()
    return True, "Model loading started in background."

def get_model():
    global MODEL
    if MODEL is None:
        # Load default synchronously if needed, or trigger background
        # For pipeline execution, we need it now.
        if MODEL_STATUS == "Not Loaded":
             load_model_background(CURRENT_MODEL_NAME)
    return MODEL

def strip_html(t):
    return re.sub(r'<.*?>', '', t)

def clean_text(t):
    t = str(t).lower()
    t = strip_html(t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return " ".join([w for w in t.split() if w not in STOP_WORDS])

def lex_score(text):
    text = str(text).lower()
    score = 0
    # Multi-word phrases
    for phrase, val in NORM_LEX.items():
        if " " in phrase and phrase in text:
            score += val * 2
    # Single word detection
    words = re.findall(r'\b[a-z0-9]+\b', text)
    for w in words:
        if w in NORM_LEX:
            val = NORM_LEX[w]
            score += val * (1.5 if val < 0 else 1)
    return max(min(score, 10), -10)

def tag_ops(text):
    tags = []
    text = str(text).lower()
    for category, words in OPERATIONAL_KEYWORDS.items():
        for w in words:
            if w in text:
                tags.append(category)
                break
    return ", ".join(tags) if tags else "general"

def run_pipeline(data_dir="data"):
    logger.info("Starting pipeline execution...")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    rows = []
    for source, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            for e in feed.entries[:50]:
                rows.append([
                    source,
                    e.get("title", ""),
                    e.get("link", ""),
                    e.get("summary", ""),
                    e.get("published", ""),
                    SEO_PRIORITY.get(source, 1)
                ])
        except Exception as err:
            logger.error(f"Error fetching {source}: {err}")

    if not rows:
        logger.warning("No data fetched.")
        return

    df = pd.DataFrame(rows, columns=["Source", "Title", "Link", "Summary", "Published", "SEO_Score"])
    df = df.drop_duplicates(subset=["Title", "Link"])
    
    # Cleaning
    df["Summary"] = df["Summary"].astype(str).apply(strip_html)
    df["Title"] = df["Title"].astype(str).apply(strip_html)
    df["cleaned"] = (df["Title"] + " " + df["Summary"]).apply(clean_text)
    df = df.drop_duplicates(subset=["Source", "cleaned"])

    # Clustering
    if not df.empty:
        model = get_model()
        emb = model.encode(df["cleaned"].tolist(), show_progress_bar=False)
        n_clusters = min(6, len(df))
        if n_clusters > 1:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
            df["topic_cluster"] = kmeans.fit_predict(emb)
        else:
            df["topic_cluster"] = 0
    else:
        df["topic_cluster"] = 0

    # Sentiment & Impact
    df["sentiment_score"] = df["cleaned"].apply(lambda x: SIA.polarity_scores(x)["compound"])
    df["lexicon_score"] = df["cleaned"].apply(lex_score)
    df["impact_score"] = (df["sentiment_score"] + df["lexicon_score"]).clip(-10, 10)
    
    df["impact_level"] = pd.cut(
        df["impact_score"],
        bins=[-12, -2, -0.3, 0.5, 2, 12],
        labels=["High Risk", "Risk", "Neutral", "Opportunity", "High Opportunity"]
    )

    # Operational Tags
    df["operational_tag"] = df["cleaned"].apply(tag_ops)

    # Event Detection
    cluster_counts = df["topic_cluster"].value_counts().to_dict()
    if cluster_counts:
        avg_volume = np.mean(list(cluster_counts.values()))
        std_volume = np.std(list(cluster_counts.values()))
    else:
        avg_volume = 0
        std_volume = 0

    def detect_event(cluster_id):
        vol = cluster_counts.get(cluster_id, 0)
        if vol > avg_volume + std_volume * 1.5:
            return "Major Event"
        elif vol > avg_volume + std_volume * 0.75:
            return "Emerging Event"
        else:
            return "Normal"

    df["event_flag"] = df["topic_cluster"].apply(detect_event)

    # Automated Cluster Naming
    try:
        def generate_cluster_names(df):
            if df.empty: return {}
            
            # Group text by cluster
            grouped = df.groupby('topic_cluster')['cleaned'].apply(lambda x: " ".join(x)).reset_index()
            
            # TF-IDF
            tfidf = TfidfVectorizer(stop_words='english', max_features=100)
            tfidf_matrix = tfidf.fit_transform(grouped['cleaned'])
            feature_names = np.array(tfidf.get_feature_names_out())
            
            cluster_names = {}
            for i, row in grouped.iterrows():
                cluster_id = row['topic_cluster']
                # Get top 3 keywords
                top_indices = tfidf_matrix[i].toarray().flatten().argsort()[::-1][:3]
                keywords = feature_names[top_indices]
                # Capitalize keywords
                name = ", ".join([k.title() for k in keywords])
                cluster_names[cluster_id] = name
            
            return cluster_names

        name_map = generate_cluster_names(df)
        df["cluster_name"] = df["topic_cluster"].map(name_map)
        # Fallback if map fails
        df["cluster_name"] = df["cluster_name"].fillna("General")
        
    except Exception as e:
        logger.error(f"Error generating cluster names: {e}")
        df["cluster_name"] = "Cluster " + df["topic_cluster"].astype(str)

    # Save final result
    output_path = os.path.join(data_dir, "final_data.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"Pipeline completed. Data saved to {output_path}")
    return output_path
