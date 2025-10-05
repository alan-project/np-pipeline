import importlib
import sys
import os
import requests
import json
from datetime import datetime, timedelta
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
from google import genai

# Add parent directory to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_local_date_range(local_tz, days_back=1):
    """Return local time range for N days back in the specified timezone"""
    # Use local timezone consistently
    now_local = datetime.now(local_tz)
    target_date = now_local - timedelta(days=days_back)

    # Local start and end times
    start_local = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    return start_local.strftime("%Y-%m-%d %H:%M:%S"), end_local.strftime("%Y-%m-%d %H:%M:%S")

def get_daily_popular_articles(config, days_back=7, limit=10):
    """Collect popular articles from the past N days"""
    db = firestore.client()
    local_tz = pytz.timezone(config["timezone"])
    result = {}
    
    for i in range(1, days_back + 1):
        start_str, end_str = get_local_date_range(local_tz, days_back=i)
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
    local_tz = pytz.timezone(config["timezone"])
    country = config["country"].lower()
    collection_name = f"{country}_daily_popular"
    
    count = 0
    for date_key, articles in daily_data.items():
        if not articles:
            print(f"{date_key} 기사 없음")
            continue

        doc = {
            'articles': articles,
            'updated_at': datetime.now(local_tz),
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

def generate_briefing_summary(top_articles, config):
    """Generate a briefing summary from top 3 articles using AI"""
    print(f"Starting briefing summary generation for {len(top_articles)} articles")

    # Initialize Gemini client
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY not found, skipping briefing")
        return None

    print(f"API key configured: {'Yes' if api_key else 'No'}")

    # Set up Gemini client (remove duplicate key to avoid warnings)
    if "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"] != api_key:
        del os.environ["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key
    client = genai.Client()

    # Get base language from config
    base_lang = config.get("base_lang", "en")
    print(f"Generating summary in base language: {base_lang}")

    # Create article list with titles
    articles_text = ""
    for i, article in enumerate(top_articles, 1):
        title = article.get('title', 'No title')
        articles_text += f"Article {i}: {title}\n"

    print(f"Top 3 articles to process:\n{articles_text}")

    prompt = f"""
Here are the top 3 most popular news articles from yesterday. Please shorten each title to a very brief phrase (under 8 words each) in {base_lang}.

{articles_text}

Requirements:
- Write in {base_lang} only
- Shorten each article title to under 8 words
- Return exactly 3 lines, one for each article
- Keep the essence of the news but make it very concise
- Do NOT include numbering or article labels
- Focus on the main topic/event

Example output format:
First article summary
Second article summary
Third article summary

Return exactly 3 shortened phrases, one per line.
"""
    
    print("Sending request to Gemini API...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )
        
        result = response.text.strip()
        print(f"AI generated briefing: '{result}'")
        print(f"Briefing length: {len(result)} characters")
        
        # Convert to numbered list - expect exactly 3 lines
        events = [event.strip() for event in result.split('\n') if event.strip()]
        
        # Ensure we have exactly 3 events
        if len(events) < 3:
            print(f"Warning: Expected 3 events but got {len(events)}")
            # Pad with empty if needed
            while len(events) < 3:
                events.append("news update")
        elif len(events) > 3:
            events = events[:3]  # Take only first 3
        
        numbered_events = [f"{i+1}. {event}" for i, event in enumerate(events)]
        final_result = ", ".join(numbered_events)
        
        print(f"Numbered briefing (3 items): '{final_result}'")
        return final_result
    except Exception as e:
        print(f"ERROR generating briefing summary: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def translate_briefing(briefing_text, target_languages, config):
    """Translate briefing summary to multiple languages"""
    if not target_languages:
        print("No target languages specified, skipping translation")
        return {}

    # Initialize Gemini client
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: GEMINI_API_KEY not found, skipping translation")
        return {}

    print(f"Translating briefing to {len(target_languages)} languages: {', '.join(target_languages)}")

    # Set up Gemini client
    if "GOOGLE_API_KEY" in os.environ and os.environ["GOOGLE_API_KEY"] != api_key:
        del os.environ["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = api_key
    client = genai.Client()

    # Create language list string
    lang_list_str = ", ".join(target_languages)

    prompt = f"""
Translate the following news briefing text into these languages: {lang_list_str}

Original text:
{briefing_text}

IMPORTANT INSTRUCTIONS:
- Translate the ENTIRE text including the numbering (1., 2., 3.)
- Keep the same format and structure
- Maintain the concise style (each item should stay brief)
- Use professional news tone for each language

Return ONLY a valid JSON object in this exact format:
{{
  "{target_languages[0]}": "translated text with 1., 2., 3.",
  "{target_languages[1] if len(target_languages) > 1 else 'placeholder'}": "translated text with 1., 2., 3."
}}

Do NOT include any explanation, markdown formatting, or additional text. Only return the JSON object.
"""

    print("Sending translation request to Gemini API...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt
        )

        result = response.text.strip()
        print(f"AI translation response: '{result}'")

        # Parse JSON response
        import json
        # Remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()

        translations = json.loads(result)
        print(f"Successfully translated to {len(translations)} languages")
        return translations

    except Exception as e:
        print(f"ERROR translating briefing: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {}

def send_briefing_push(title, messages, country):
    """Send briefing push notification via Firebase function

    Args:
        title: Push notification title
        messages: Multilingual briefing messages dict (e.g., {"de": "...", "ro": "...", "ar": "..."})
                 or string for backward compatibility
        country: Country code (e.g., "ca", "de", "sa")
    """
    function_url = os.getenv("FIREBASE_FUNCTION_URL") or "https://sendbriefingpushbycountry-ladydgb7za-uc.a.run.app"

    payload = {
        "title": title,
        "messages": messages,  # Send as multilingual object
        "country": country
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending push notification to {country}")
    print(f"Payload: title='{title}', messages type={type(messages).__name__}, country='{country}'")

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
    # Use local timezone consistently
    local_now = datetime.now(local_tz)
    yesterday = local_now - timedelta(days=1)
    yesterday_key = yesterday.strftime("%Y-%m-%d")
    
    yesterday_articles = daily_data.get(yesterday_key, [])
    
    if not yesterday_articles:
        print(f"No articles found for yesterday ({yesterday_key}), skipping briefing")
        print(f"Available dates in daily_data: {list(daily_data.keys())}")
        print(f"Local timezone: {config['timezone']}, Current local time: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
        return
    
    # Extract top 3 articles only
    top_3_articles = yesterday_articles[:3]
    
    if not top_3_articles:
        print("No articles found, skipping briefing")
        return
    
    print(f"Processing top {len(top_3_articles)} articles for briefing")
    
    # Generate briefing summary for top 3 articles in base language
    briefing_message = generate_briefing_summary(top_3_articles, config)

    if not briefing_message:
        print("Failed to generate briefing summary")
        return

    # Get base language and supported languages
    base_lang = config.get("base_lang", "en")
    lang_list = config.get("lang_list", [])

    # Start with base language
    multilingual_briefing = {
        base_lang: briefing_message
    }

    print(f"Base language briefing ({base_lang}): {briefing_message}")

    # Translate to other supported languages
    if lang_list:
        print(f"Translating briefing to {len(lang_list)} additional languages")
        translations = translate_briefing(briefing_message, lang_list, config)

        if translations:
            # Merge translations with base language
            multilingual_briefing.update(translations)
            print(f"Total languages in briefing: {len(multilingual_briefing)}")
        else:
            print("Translation failed, sending base language only")
    else:
        print("No additional languages to translate, sending base language only")

    # Send push notification with yesterday's date
    yesterday_date = yesterday.strftime("%B %d") # e.g., "January 15"
    # push_title = f"Yesterday's News ({yesterday_date})"
    push_title = f"Quick News Recap"

    country_code = config["country"].lower()
    if country_code == "saudi":
        country_code = "sa"  # Convert saudi to sa for country code

    # Log data to be sent to server
    print("\n" + "="*60)
    print("Data to be sent to server")
    print("="*60)
    print(f"Title: {push_title}")
    print(f"Country code: {country_code}")
    print(f"\nMultilingual briefing messages:")
    print("-"*60)
    for lang, msg in multilingual_briefing.items():
        print(f"  [{lang}]: {msg}")
    print("="*60 + "\n")

    # Send push notification to server
    success = send_briefing_push(push_title, multilingual_briefing, country_code)

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
    local_tz = pytz.timezone(config["timezone"])
    print(f"START TIME: {datetime.now(local_tz).strftime('%Y-%m-%d %H:%M:%S')} {config['timezone']}")

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