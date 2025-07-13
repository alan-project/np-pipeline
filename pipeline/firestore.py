import firebase_admin
import os
from firebase_admin import credentials, firestore
from datetime import datetime
import pytz

def save_to_server(data, config):
    """Save processed articles to Firestore"""
    db = firestore.client()
    collection_name = config["firestore_collection"]
    
    for article in data:
        if not article:
            continue
        article_id = article["article_id"]
        db.collection(collection_name).document(article_id).set(article)
        print(f"update success: {article_id}")
    
    try:
        meta_collection = config["info_doc"]
        db.collection(meta_collection).document("meta").set({
            "lastUpdatedAt": datetime.now()
        }, merge=True)
        print("meta data updated")
    except Exception as e:
        print(f"metadata update fail: {e}")


def save_article_stats(total_articles, uploaded_articles, config):
    """Save article statistics to Firestore with local timezone"""
    db = firestore.client()
    info_collection = config["info_doc"]
    
    # Get local time based on config timezone
    local_tz = pytz.timezone(config['timezone'])
    local_time = datetime.now(local_tz)
    
    # Format date and hour
    date_str = local_time.strftime('%Y-%m-%d')
    hour_str = local_time.strftime('%H')
    
    # Document structure: {date}/{hour}
    doc_ref = db.collection(info_collection).document(date_str)
    
    # Update hourly stats
    doc_ref.set({
        f"hours.{hour_str}": {
            "total_articles": total_articles,
            "uploaded_articles": uploaded_articles,
            "timestamp": local_time
        }
    }, merge=True)
    
    print(f"Stats saved: {date_str} {hour_str}:00 - Total: {total_articles}, Uploaded: {uploaded_articles}")