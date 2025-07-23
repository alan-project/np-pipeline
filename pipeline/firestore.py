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
    
    # Check if this is the first action of the day - calculate previous day totals
    if is_first_action_of_day(db, info_collection, date_str, hour_str):
        calculate_previous_day_totals(db, info_collection, local_time, local_tz)


def is_first_action_of_day(db, info_collection, date_str, current_hour_str):
    """Check if this is the first action (hour entry) of the current day"""
    try:
        doc_ref = db.collection(info_collection).document(date_str)
        doc = doc_ref.get()
        
        if not doc.exists:
            print(f"DEBUG: Document for {date_str} doesn't exist yet - this is the first action")
            return True
        
        data = doc.to_dict()
        hours_data = data.get('hours', {})
        
        # Check if there are any hours recorded before the current hour
        current_hour = int(current_hour_str)
        existing_hours = [int(hour) for hour in hours_data.keys() if hour.isdigit()]
        
        if not existing_hours:
            print(f"DEBUG: No existing hours for {date_str} - this is the first action")
            return True
        
        # Check if current hour is the earliest hour recorded today
        min_existing_hour = min(existing_hours)
        is_first = current_hour <= min_existing_hour
        
        print(f"DEBUG: Date {date_str}, Current hour: {current_hour}, Existing hours: {sorted(existing_hours)}, Is first: {is_first}")
        return is_first
        
    except Exception as e:
        print(f"DEBUG: Error checking first action of day: {e}")
        # If there's an error, assume it's the first action to be safe
        return True


def calculate_previous_day_totals(db, info_collection, current_time, local_tz):
    """Calculate and save total statistics for the previous day"""
    try:
        # Get previous day
        previous_day = current_time - timedelta(days=1)
        prev_date_str = previous_day.strftime('%Y-%m-%d')
        
        print(f"Calculating daily totals for {prev_date_str}...")
        
        # Get previous day's document
        prev_doc_ref = db.collection(info_collection).document(prev_date_str)
        prev_doc = prev_doc_ref.get()
        
        if not prev_doc.exists:
            print(f"No data found for {prev_date_str}")
            return
        
        data = prev_doc.to_dict()
        print(f"DEBUG: Document data structure: {data}")
        
        hours_data = data.get('hours', {})
        print(f"DEBUG: Hours data: {hours_data}")
        
        if not hours_data:
            print(f"No hourly data found for {prev_date_str}")
            return
        
        # Calculate totals
        total_articles_sum = 0
        uploaded_articles_sum = 0
        
        print(f"DEBUG: Processing {len(hours_data)} hours of data...")
        for hour, stats in hours_data.items():
            print(f"DEBUG: Hour {hour}, Stats: {stats}")
            print(f"DEBUG: Stats type: {type(stats)}")
            
            if isinstance(stats, dict):
                total_articles = stats.get('total_articles', 0)
                uploaded_articles = stats.get('uploaded_articles', 0)
                print(f"DEBUG: Hour {hour} - total: {total_articles}, uploaded: {uploaded_articles}")
                total_articles_sum += total_articles
                uploaded_articles_sum += uploaded_articles
            else:
                print(f"DEBUG: Hour {hour} - stats is not a dict: {stats}")
        
        print(f"DEBUG: Final sums - Total: {total_articles_sum}, Uploaded: {uploaded_articles_sum}")
        
        # Save daily totals in result subcollection
        result_data = {
            "total_articles": total_articles_sum,
            "uploaded_articles": uploaded_articles_sum,
            "date": prev_date_str,
            "calculated_at": current_time
        }
        
        # Save to result subcollection
        prev_doc_ref.set({
            "result": result_data
        }, merge=True)
        
        print(f"Daily totals saved for {prev_date_str}: Total: {total_articles_sum}, Uploaded: {uploaded_articles_sum}")
        
    except Exception as e:
        print(f"Error calculating previous day totals: {e}")
        import traceback
        print(f"DEBUG: Full traceback: {traceback.format_exc()}")