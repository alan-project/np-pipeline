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
                .order_by("clicked_cnt", direction=firestore.Query.DESCENDING) \
                .limit(limit) \
                .stream()

            articles = []
            for doc in snapshot:
                data = doc.to_dict()
                if 'article_id' not in data:
                    data['article_id'] = doc.id
                articles.append(data)

            result[date_key] = articles
            print(f"{date_key}: {len(articles)} popular articles")

        except Exception as e:
            print(f"Error fetching articles for {date_key}: {e}")
            result[date_key] = []

    return result

def save_daily_popular_to_firestore(daily_data, config):
    """Save daily popular articles to Firestore"""
    db = firestore.client()
    utc_timezone = pytz.timezone('UTC')
    country = config["country"].lower()
    collection_name = f"{country}_daily_popular"
    
    count = 0
    for date_key, articles in daily_data.items():
        if not articles:
            print(f"{date_key} 기사 없음")
            continue

        doc = {
            'articles': articles,
            'updated_at': datetime.now(utc_timezone),
            'count': len(articles),
            'date': date_key
        }

        try:
            db.collection(collection_name).document(date_key).set(doc)
            print(f"{date_key} 저장 완료 ({len(articles)}개)")
            count += 1
        except Exception as e:
            print(f"{date_key} 저장 오류: {e}")
    
    return count

def generate_briefing_summary(article_titles, config):
    """Generate a briefing summary from article titles using AI"""
    print(f"Starting briefing summary generation for {len(article_titles)} articles")
    
    api_url = os.getenv("AI_URL")
    api_key = config.get("api_key") or os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_url or not api_key:
        print("ERROR: AI_URL or API_KEY not found, skipping briefing")
        return None
    
    print(f"Using AI API URL: {api_url}")
    print(f"API key configured: {'Yes' if api_key else 'No'}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Join article titles
    titles_text = "\n".join([f"- {title}" for title in article_titles])
    print(f"Article titles to process:\n{titles_text}")
    
    prompt = f"""
Look at these news article titles from yesterday's most popular news and list the key events in English.

Article titles:
{titles_text}

Requirements:
- Write in English only
- List 2-3 most important events/topics in simple phrases
- Separate each event with comma and space
- Keep each event description under 10 words
- Focus on the most significant news only
- Be concise and specific
- Do NOT include any prefix or format text, just the event list

Example: "serious traffic accident, government policy announcement, local protest"

If no significant news is found, return: "no major updates"
"""
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.3
    }
    
    print("Sending request to AI API...")
    try:
        response = requests.post(api_url, headers=headers, json=data)
        print(f"AI API response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json().get("choices", [])[0].get("message", {}).get("content", "").strip()
            print(f"AI generated briefing: '{result}'")
            print(f"Briefing length: {len(result)} characters")
            return result
        else:
            print(f"AI API failed with status {response.status_code}")
            print(f"Response text: {response.text}")
            return None
    except Exception as e:
        print(f"ERROR generating briefing summary: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def send_briefing_push(title, message, country):
    """Send briefing push notification via Firebase function"""
    function_url = os.getenv("FIREBASE_FUNCTION_URL") or "https://your-function-url/sendBriefingPushByCountry"
    
    payload = {
        "title": title,
        "message": message,
        "country": country
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(function_url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"Push notification sent successfully to {country}")
            return True
        else:
            print(f"Failed to send push notification: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error sending push notification: {e}")
        return False

def send_yesterday_briefing(daily_data, config):
    """Send briefing push for yesterday's popular articles"""
    local_tz = pytz.timezone(config["timezone"])
    yesterday = datetime.now(local_tz) - timedelta(days=1)
    yesterday_key = yesterday.strftime("%Y-%m-%d")
    
    yesterday_articles = daily_data.get(yesterday_key, [])
    
    if not yesterday_articles:
        print(f"No articles found for yesterday ({yesterday_key}), skipping briefing")
        return
    
    # Extract titles from articles
    article_titles = []
    for article in yesterday_articles[:10]:  # Limit to top 10
        title = article.get('title', '')
        if title:
            article_titles.append(title)
    
    if not article_titles:
        print("No article titles found, skipping briefing")
        return
    
    print(f"Processing {len(article_titles)} article titles for briefing")
    
    # Generate briefing summary
    briefing_message = generate_briefing_summary(article_titles, config)
    
    if not briefing_message:
        print("Failed to generate briefing summary")
        return
    
    # Send push notification
    push_title = "Today's News Briefing"
    # Add prefix to the briefing message
    final_message = f"Don't miss yesterday's updates: {briefing_message}"
    
    country_code = config["country"].lower()
    if country_code == "saudi":
        country_code = "sa"  # Convert saudi to sa for country code
    
    success = send_briefing_push(push_title, final_message, country_code)
    
    if success:
        print("Briefing push sent successfully")
    else:
        print("Failed to send briefing push")

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
    updated = save_daily_popular_to_firestore(daily_data, config)
    
    print(f"총 {updated}개 날짜의 문서 업데이트 완료")
    
    # Send briefing push for yesterday's popular articles
    print("Sending briefing push notification...")
    send_yesterday_briefing(daily_data, config)
    
    print("Daily popular pipeline DONE")

if __name__ == "__main__":
    main()