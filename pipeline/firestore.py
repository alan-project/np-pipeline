import firebase_admin
import os
from firebase_admin import credentials, firestore
from datetime import datetime

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