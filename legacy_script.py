seo_priority = {
     "Ada Derana": 10,
    "Daily Mirror": 10,
    "Lankadeepa": 9,
    "The Island": 8,
    "Divaina": 8,
    "Thinakaran": 8,
    "Sunday Times": 8,
    "Dinamina": 7,
    "Virakesari": 7,
    "Daily News": 6,
    "Silumina": 6,
    "EconomyNext": 5,
    "FT.LK": 4,
    "LankaBusinessOnline": 3,
    "News.lk": 2,
    "Ceylon Today": 1,
    "ITN News": 1,
    "Onlanka.com": 1
}

rss_feeds = {
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


import feedparser
import pandas as pd

rows = []

for source, url in rss_feeds.items():
    try:
        feed = feedparser.parse(url)
        for e in feed.entries[:50]:
            rows.append([
                source,
                e.get("title", ""),
                e.get("link", ""),
                e.get("summary", ""),
                seo_priority.get(source, 1)
            ])
    except Exception as err:
        print("Error:", source, err)

df = pd.DataFrame(rows, columns=["Source", "Title", "Link", "Summary", "SEO_Score"])
df = df.drop_duplicates(subset=["Title", "Link"])

df.to_csv("raw_news.csv", index=False)

import re
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

def strip_html(t):
    return re.sub(r'<.*?>', '', t)

def clean_text(t):
    t = t.lower()
    t = strip_html(t)
    t = re.sub(r'[^a-z0-9\s]', ' ', t)
    return " ".join([w for w in t.split() if w not in stop_words])

df = pd.read_csv("raw_news.csv")
df["Summary"] = df["Summary"].astype(str).apply(strip_html)
df["Title"] = df["Title"].astype(str).apply(strip_html)
df["cleaned"] = (df["Title"] + " " + df["Summary"]).apply(clean_text)

df = df.drop_duplicates(subset=["Source", "cleaned"])
df.to_csv("cleaned_news.csv", index=False)

from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans

df = pd.read_csv("cleaned_news.csv")

model = SentenceTransformer("all-MiniLM-L6-v2",  device="cuda")
emb = model.encode(df["cleaned"].tolist(), show_progress_bar=True)

# Avoid cluster error for small datasets
n_clusters = min(6, len(df))

kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
df["topic_cluster"] = kmeans.fit_predict(emb)

df.to_csv("clustered_news.csv", index=False)

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()

df = pd.read_csv("clustered_news.csv")

df["sentiment_score"] = df["cleaned"].apply(lambda x: sia.polarity_scores(x)["compound"])

df.to_csv("sentiment_news.csv", index=False)

lexicon = {

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

    "quarantine": -2,
    "outage": -2,
    "power_cut": -2,
    "transport_strike": -2,
    "road_accident": -2,
    "fuel_shortage": -2,
    "water_shortage": -2,
    "pollution_alert": -2,
    "traffic_disruption": -2,
    "inflation": -2,
    "loss": -2,
    "tourism_decline": -2,
    "health_alert": -2,
    "infection": -2,
    "infection_rate": -2,
    "congestion": -1,

    "power_outage": -2,
    "galle_bridge_collapse": -3,
    "colombo_airport_delay": -2,
    "attack": -3,
    "crime": -2,
    "arrest": -2,
    "terror": -3,
    "violence": -3,
    "conflict": -3,
    "robbery": -2,
    "burglary": -2,
    "assault": -2,
    "kidnap": -3,
    "hijack": -3,
    "illegal_activity": -2,
    "law_violation": -2,
    "risk_alert": -1,
    "threat": -2,

    "pollution": -2,
    "air_quality": -2,
    "climate_change": -1,

    "colombo_flood": -3,
    "kandy_protest": -2,
    "galle_traffic": -1,
    "negombo_storm": -2,
    "anuradhapura_drought": -2,
    "panadura_flood": -3,
    "kurunegala_traffic": -1,
    "matara_flood": -3,
    "colombo_protest": -2,

    "economic_crash": -3,
    "inflation_spike": -3,
    "currency_devaluation": -3,


    # POSITIVE (OPPORTUNITY)
    "donation": 2,
    "aid": 2,
    "relief": 2,
    "funding": 2,
    "charity": 2,
    "assistance": 2,
    "grant": 2,
    "shelter": 2,

    "medical_support": 2,
    "rescue_team": 2,
    "volunteer": 2,
    "food_distribution": 2,
    "emergency_fund": 2,
    "rebuilding": 2,
    "recovery": 2,
    "rehabilitation": 2,
    "community_help": 2,
    "ngo_project": 2,

    "initiative": 1,
    "announcement": 1,
    "resolution": 1,
    "strategy": 1,
    "policy_update": 1,
    "regulatory_change": 1,
    "government_order": 1,

    "investment": 2,
    "trade": 2,
    "profit": 2,
    "revenue": 2,
    "export": 2,
    "business_growth": 2,
    "economic_upturn": 2,
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

    "tea_export": 2,
    "garment_industry": 2,
    "tourism_growth": 2,
    "foreign_investment": 2,
    "industrial_development": 2,
    "business_partnership": 2,
    "market_expansion": 2,
    "revenue_increase": 3,
    "profit_record": 3,

    "disease_control": 2,
    "healthcare_improvement": 2,
    "medical_facility_upgrade": 2,

    "infrastructure_development": 2,
    "infrastructure_upgrade": 2,
    "project_completion": 2,
    "energy_supply": 2,
    "utility_service": 1,

    "patrol": 1,
    "public_safety": 1,

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

    "ratnapura_tea_export": 2,
    "tea_export_success": 2,
    "garment_factory_opening": 2,
    "tourism_peak": 2,
    "foreign_aid_received": 2,
    "infrastructure_grant": 2,
    "startup_funding": 2
}
import re

# normalize (convert underscores to spaces)
norm_lex = {k.replace("_", " "): v for k, v in lexicon.items()}

def lex_score(text):
    text = text.lower()
    score = 0

    # --- Multi-word phrases ---
    for phrase, val in norm_lex.items():
        if " " in phrase and phrase in text:
            score += val * 2

    # --- Single word detection ---
    words = re.findall(r'\b[a-z0-9]+\b', text)

    for w in words:
        if w in norm_lex:
            val = norm_lex[w]
            score += val * (1.5 if val < 0 else 1)

    # clamp
    return max(min(score, 10), -10)


df = pd.read_csv("sentiment_news.csv")
df["lexicon_score"] = df["cleaned"].apply(lex_score)

df.to_csv("lex_scored_news.csv", index=False)

df = pd.read_csv("lex_scored_news.csv")

df["impact_score"] = df["sentiment_score"] + df["lexicon_score"]
df["impact_score"] = df["impact_score"].clip(-10, 10)

df.to_csv("impact_news.csv", index=False)

df = pd.read_csv("impact_news.csv")

df["impact_level"] = pd.cut(
    df["impact_score"],
    bins=[-12, -2, -0.3, 0.5, 2, 12],
    labels=["High Risk", "Risk", "Neutral", "Opportunity", "High Opportunity"]
)

df.to_csv("final_scored_news.csv", index=False)

import numpy as np
operational_keywords = {
    "weather": ["flood", "storm", "cyclone", "landslide"],
    "transport": ["traffic", "accident", "train", "bus delay"],
    "utilities": ["outage", "power", "water cut"],
    "health": ["disease", "infection", "hospital"],
    "security": ["crime", "arrest", "violence", "attack"],
    "economic": ["inflation", "investment", "trade", "market"]
}

def tag_ops(text):
    tags = []
    for category, words in operational_keywords.items():
        for w in words:
            if w in text.lower():
                tags.append(category)
                break
    return ", ".join(tags) if tags else "general"

df["operational_tag"] = df["cleaned"].apply(tag_ops)

cluster_counts = df["topic_cluster"].value_counts().to_dict()
avg_volume = np.mean(list(cluster_counts.values()))
std_volume = np.std(list(cluster_counts.values()))

def detect_event(cluster_id):
    vol = cluster_counts.get(cluster_id, 0)
    if vol > avg_volume + std_volume * 1.5:
        return "Major Event"
    elif vol > avg_volume + std_volume * 0.75:
        return "Emerging Event"
    else:
        return "Normal"

df["event_flag"] = df["topic_cluster"].apply(detect_event)

df.to_csv("final_with_events.csv", index=False)
