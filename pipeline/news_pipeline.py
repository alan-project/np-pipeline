import importlib
import sys
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to Python path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize Firebase first before importing other modules
import firebase_admin
from firebase_admin import credentials, firestore

from pipeline.summarize import generate_ai_summary
from pipeline.translate import translate_ai_summary
from pipeline.firestore import save_to_server
from pipeline.util import get_page_articles, fetch_articles, select_top_articles

def process_article(article, config, api_key):
    content = article.get("content")
    if not content:
        print(f"no content: article ID {article['article_id']}")
        return None

    ai_summary = generate_ai_summary(content, {**config, "api_key": api_key})
    if not ai_summary:
        print(f"article ID {article['article_id']} summary fail")
        return None

    article.update(ai_summary)

    translations = {}
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            lang: executor.submit(
                translate_ai_summary,
                ai_summary["ai_title"],
                ai_summary["ai_content"],
                lang,
                {**config, "api_key": api_key}
            ) for lang in config["lang_list"]
        }
        for lang, future in futures.items():
            result = future.result()
            if not result:
                print(f"article ID {article['article_id']} -> {lang} translation fail")
                return None
            translations[lang] = result

    translations["en"] = {
        "ai_title": ai_summary["ai_title"],
        "ai_content": ai_summary["ai_content"]
    }
    article["translations"] = translations
    article["clicked_cnt"] = 0

    print(f"article ID {article['article_id']} processed")
    return article


def main():
    if len(sys.argv) < 2:
        print("Usage: python news_pipeline.py <country>")
        sys.exit(1)

    country = sys.argv[1].lower()

    # Load security keys from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    
    firebase_cred_path = os.getenv("FIREBASE_CREDENTIAL_PATH")
    if not firebase_cred_path:
        raise ValueError("FIREBASE_CREDENTIAL_PATH is not set.")
    
    # Initialize Firebase Admin SDK
    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_cred_path)
        firebase_admin.initialize_app(cred)
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_cred_path

    # Load country-specific configuration
    config_module = importlib.import_module(f"configs.{country}")
    config = config_module.config

    print(f"Running pipeline for: {config['country']}")
    print(f"START TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    results = fetch_articles(config["api_url"], api_key, config)
    print(f"Processed {len(results)} articles")

    save_to_server(results, config)
    print("DONE")


if __name__ == "__main__":
    main()
