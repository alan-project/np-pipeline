import importlib
import sys
import os
from datetime import datetime, timedelta
import pytz
import firebase_admin
from firebase_admin import credentials, firestore

# Add parent directory to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_utc_range_of_local_yesterday(local_tz, days_back=1):
    """Return UTC time range for N days back in the specified timezone"""
    now_local = datetime.now(local_tz)
    target_date = now_local - timedelta(days=days_back)

    # Local start and end times
    start_local = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # Convert to UTC
    start_utc = start_local.astimezone(pytz.utc)
    end_utc = end_local.astimezone(pytz.utc)

    return start_utc.strftime("%Y-%m-%d %H:%M:%S"), end_utc.strftime("%Y-%m-%d %H:%M:%S")

def get_daily_popular_articles(config, days_back=7, limit=10):
    """Collect popular articles from the past N days"""
    db = firestore.client()
    local_tz = pytz.timezone(config["timezone"])
    result = {}
    
    for i in range(1, days_back + 1):
        start_str, end_str = get_utc_range_of_local_yesterday(local_tz, days_back=i)
        date_key = start_str.split(" ")[0]  # YYYY-MM-DD

        try:
            snapshot = db.collection(config["firestore_collection"]) \
                .where("pubDate", ">=", start_str) \
                .where("pubDate", "<=", end_str) \
                .where("clicked_cnt", ">", 0) \
                .order_by("clicked_cnt", direction=firestore.Query.DESCENDING) \
                .limit(limit) \
                .stream()

            articles = []
            for doc in snapshot:
                data = doc.to_dict()
                articles.append({
                    "article_id": data.get("article_id"),
                    "title": data.get("title"),
                    "ai_title": data.get("ai_title"),
                    "ai_content": data.get("ai_content"),
                    "category_ai": data.get("category_ai"),
                    "clicked_cnt": data.get("clicked_cnt", 0),
                    "pubDate": data.get("pubDate"),
                    "link": data.get("link"),
                    "translations": data.get("translations", {})
                })

            result[date_key] = articles
            print(f"{date_key}: {len(articles)} popular articles")

        except Exception as e:
            print(f"Error fetching articles for {date_key}: {e}")
            result[date_key] = []

    return result

def save_daily_popular_to_firestore(daily_data, config):
    """Save daily popular articles to Firestore"""
    db = firestore.client()
    
    try:
        # Save all daily data as a single document
        db.collection(config["info_doc"]).document("daily_popular").set({
            "daily_data": daily_data,
            "lastUpdatedAt": datetime.now(),
            "generated_by": "daily_popular_pipeline"
        })
        
        print(f"Daily popular data saved to {config['info_doc']}/daily_popular")
        
        # Save summary statistics
        total_articles = sum(len(articles) for articles in daily_data.values())
        db.collection(config["info_doc"]).document("daily_popular_meta").set({
            "total_days": len(daily_data),
            "total_articles": total_articles,
            "lastUpdatedAt": datetime.now(),
            "country": config["country"]
        }, merge=True)
        
        print(f"Saved {total_articles} articles across {len(daily_data)} days")
        
    except Exception as e:
        print(f"Error saving to Firestore: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python daily_popular_pipeline.py <country>")
        sys.exit(1)

    country = sys.argv[1].lower()

    # Initialize Firebase
    firebase_cred_path = os.getenv("FIREBASE_CREDENTIAL_PATH")
    if not firebase_cred_path:
        raise ValueError("FIREBASE_CREDENTIAL_PATH is not set.")
    
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)

    # Load country-specific configuration
    config_module = importlib.import_module(f"configs.{country}")
    config = config_module.config

    print(f"Running daily popular pipeline for: {config['country']}")
    print(f"START TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    # Collect popular articles from the past 7 days
    days_back = config.get("daily_popular_days", 7)
    limit_per_day = config.get("daily_popular_limit", 10)
    
    daily_data = get_daily_popular_articles(config, days_back=days_back, limit=limit_per_day)
    
    # Save to Firestore
    save_daily_popular_to_firestore(daily_data, config)
    
    print("Daily popular pipeline DONE")

if __name__ == "__main__":
    main()