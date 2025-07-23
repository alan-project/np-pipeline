import firebase_admin
import os
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
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
    """Save article statistics to Firestore with local timezone and update daily totals"""
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
    
    # Update daily totals based on current result folder values
    update_daily_totals(db, info_collection, date_str, total_articles, uploaded_articles)


def update_daily_totals(db, info_collection, date_str, new_total_articles, new_uploaded_articles):
    """Update daily totals by reading existing result and adding new values"""
    try:
        doc_ref = db.collection(info_collection).document(date_str)
        doc = doc_ref.get()
        
        # Initialize totals
        current_total = 0
        current_uploaded = 0
        
        # If document exists and has result data, read existing totals
        if doc.exists:
            data = doc.to_dict()
            result_data = data.get('result', {})
            
            if result_data:
                current_total = result_data.get('total_articles', 0)
                current_uploaded = result_data.get('uploaded_articles', 0)
                print(f"Found existing totals for {date_str}: Total: {current_total}, Uploaded: {current_uploaded}")
        
        # Add new values to existing totals
        updated_total = current_total + new_total_articles
        updated_uploaded = current_uploaded + new_uploaded_articles
        
        # Save updated totals to result
        result_data = {
            "total_articles": updated_total,
            "uploaded_articles": updated_uploaded,
            "date": date_str,
            "last_updated": datetime.now()
        }
        
        doc_ref.set({
            "result": result_data
        }, merge=True)
        
        print(f"Daily totals updated for {date_str}: Total: {updated_total} (+{new_total_articles}), Uploaded: {updated_uploaded} (+{new_uploaded_articles})")
        
    except Exception as e:
        print(f"Error updating daily totals: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")