import importlib
import sys
import os
import requests
import json
from datetime import datetime, timedelta
import pytz
import firebase_admin
from firebase_admin import credentials, firestore

# Add parent directory to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration constants
DEFAULT_HOURS_BACK = 6  # Hours to look back for popular articles
FIREBASE_FUNCTION_URL = os.getenv("FIREBASE_FUNCTION_URL") or "https://us-central1-the-north-news.cloudfunctions.net/sendArticlePushByLanguage"

def get_time_range(local_tz, hours_back=DEFAULT_HOURS_BACK):
    """Return local time range for N hours back in the specified timezone"""
    now_local = datetime.now(local_tz)
    start_time = now_local - timedelta(hours=hours_back)

    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    end_str = now_local.strftime("%Y-%m-%d %H:%M:%S")

    return start_str, end_str

def get_most_popular_article(config, hours_back=DEFAULT_HOURS_BACK):
    """Get the most popular article from the past N hours based on click count"""
    db = firestore.client()
    local_tz = pytz.timezone(config["timezone"])

    start_str, end_str = get_time_range(local_tz, hours_back)

    print(f"Searching for articles between {start_str} and {end_str} in {config['timezone']}")

    try:
        # Query articles from the specified time range, ordered by click count descending
        snapshot = db.collection(config["firestore_collection"]) \
            .where("pubDate", ">=", start_str) \
            .where("pubDate", "<=", end_str) \
            .order_by("clicked_cnt", direction=firestore.Query.DESCENDING) \
            .limit(1) \
            .stream()

        articles = []
        doc_ids = []
        for doc in snapshot:
            data = doc.to_dict()
            if 'article_id' not in data:
                data['article_id'] = doc.id
            articles.append(data)
            doc_ids.append(doc.id)

        if articles:
            article = articles[0]
            doc_id = doc_ids[0]
            print(f"Found most popular article: {article.get('title', 'No title')} (clicks: {article.get('clicked_cnt', 0)})")
            print(f"📊 Article debug info:")
            print(f"   - Collection: {config['firestore_collection']}")
            print(f"   - Document ID: {doc_id}")
            print(f"   - article_id field: {article.get('article_id', 'MISSING')}")
            print(f"   - id field: {article.get('id', 'MISSING')}")
            print(f"   - pubDate: {article.get('pubDate', 'MISSING')}")
            print(f"   - All keys in article: {list(article.keys())}")
            return article
        else:
            print(f"No articles found in the specified time range for {config['country']}")
            return None

    except Exception as e:
        print(f"Error fetching articles for {config['country']}: {e}")
        return None

def send_push_notification(article_id, country_code):
    """Send push notification via Firebase function"""

    # Firebase function expects full country names, not country codes
    # Keep the original country name
    final_country_code = country_code.lower()

    payload = {
        "articleId": article_id,
        "header": "News Platter",  # You can customize this header
        "country": final_country_code
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        print(f"🚀 Sending push notification:")
        print(f"   - Firebase Function URL: {FIREBASE_FUNCTION_URL}")
        print(f"   - Article ID: {article_id}")
        print(f"   - Country Code: {final_country_code}")
        print(f"   - Original Country: {country_code}")
        print(f"   - Headers: {json.dumps(headers, indent=2)}")
        print(f"   - Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(FIREBASE_FUNCTION_URL, headers=headers, json=payload)

        print(f"📡 Firebase Function Response:")
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Headers: {dict(response.headers)}")
        print(f"   - Response Text: {response.text}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Push notification sent successfully!")
            print(f"   - Success count: {result.get('successCount', 0)}")
            print(f"   - Failure count: {result.get('failureCount', 0)}")
            print(f"   - Ignored users: {result.get('ignoredUsers', 0)}")
            return True
        else:
            print(f"❌ Failed to send push notification: {response.status_code}")
            print(f"   - Error response: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python push_notification_pipeline.py <country> [hours_back]")
        print("Example: python push_notification_pipeline.py uae 6")
        sys.exit(1)

    country = sys.argv[1].lower()

    # Optional hours_back parameter
    hours_back = DEFAULT_HOURS_BACK
    if len(sys.argv) >= 3:
        try:
            hours_back = int(sys.argv[2])
            print(f"Using custom hours_back: {hours_back}")
        except ValueError:
            print(f"Invalid hours_back parameter. Using default: {DEFAULT_HOURS_BACK}")

    # Initialize Firebase
    firebase_cred_path = os.getenv("FIREBASE_CREDENTIAL_PATH")
    if not firebase_cred_path:
        raise ValueError("FIREBASE_CREDENTIAL_PATH is not set.")

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)

    # Load country-specific configuration
    try:
        config_module = importlib.import_module(f"configs.{country}")
        config = config_module.config
    except ImportError:
        print(f"Configuration for country '{country}' not found.")
        print("Available countries: uae, saudi, canada, germany, russia")
        sys.exit(1)

    print(f"Running push notification pipeline for: {config['country']}")
    local_tz = pytz.timezone(config["timezone"])
    print(f"START TIME: {datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')} {config['timezone']}")
    print(f"Looking back {hours_back} hours for most popular article")

    # Get the most popular article from the specified time range
    article = get_most_popular_article(config, hours_back)

    if not article:
        print("No article found to send push notification for.")
        return

    # Extract article ID
    article_id = article.get('article_id') or article.get('id')
    if not article_id:
        print("Article ID not found in article data.")
        return

    # Send push notification
    success = send_push_notification(article_id, country)

    if success:
        print("Push notification pipeline completed successfully!")
    else:
        print("Push notification pipeline failed!")

    print("Push notification pipeline DONE")

if __name__ == "__main__":
    main()