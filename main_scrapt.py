import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
from flask import Flask, render_template, jsonify
from datetime import datetime
from collections import Counter
from apify_client import ApifyClient

app = Flask(__name__)

OUTPUT_FOLDER = 'scraped_data_results'
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# Tentukan nama file JSON lokal yang kamu miliki sebagai database sementara
LOCAL_JSON_DATASET = 'dataset_instagram-hashtag-scraper_2026-05-05_12-49-49-187.json'

# Filter Noise: Abaikan hashtag umum yang tidak memberikan ide topik spesifik
STOP_HASHTAGS = {
    'viral', 'fyp', 'fypシ', 'foryou', 'foryoupage', 'trendingnow', 'trending',
    'explore', 'explorepage', 'instagram', 'instagood', 'post', 'photography',
    'viralpost', 'reels', 'reelsindia', 'viralreels', 'v', 'share', 'like', 'follow'
}

def get_apify_token():
    try:
        tree = ET.parse('config.xml')
        root = tree.getroot()
        return root.find('apify/api_token').text
    except Exception as e:
        print(f"Error XML: {e}")
        return None

def run_actual_scraping():
    token = get_apify_token()
    if not token:
        return None, "Token tidak valid"

    client = ApifyClient(token)
    try:
        run_input = {
            "hashtags": ["fyp"],
            "resultsLimit": 20,
        }
        run = client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        df = pd.DataFrame(items)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"apify_result_{timestamp}.csv"
        save_path = os.path.join(OUTPUT_FOLDER, filename)
        df.to_csv(save_path, index=False)
        
        return items, None
    except Exception as e:
        return None, str(e)

def process_hashtag_trends(posts_data):
    """Fungsi Analitor untuk menyaring dan menghitung tren hashtag spesifik"""
    all_hashtags = []
    for post in posts_data:
        tags = post.get('hashtags', [])
        if isinstance(tags, list):
            for tag in tags:
                clean_tag = tag.lower().strip()
                # Hanya masukkan jika tidak ada di dalam list kata sampah
                if clean_tag and clean_tag not in STOP_HASHTAGS:
                    all_hashtags.append(clean_tag)
    
    top_10 = Counter(all_hashtags).most_common(10)
    return [{"hashtag": h, "count": c} for h, c in top_10]

@app.route('/')
def index():
    # Merender halaman utama website
    return render_template('index.html')

@app.route('/api/trends', methods=['GET'])
def get_local_trends():
    """Mengolah dan menampilkan tren dari file JSON lokal yang kamu berikan"""
    if not os.path.exists(LOCAL_JSON_DATASET):
        return jsonify({"status": "error", "message": "File JSON dataset tidak ditemukan di root folder."}), 404
        
    try:
        with open(LOCAL_JSON_DATASET, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        
        trend_results = process_hashtag_trends(posts_data)
        return jsonify({
            "status": "success",
            "source": "local_json",
            "data": trend_results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/scrape', methods=['POST'])
def handle_scrape():
    """Rute untuk menjalankan live scraping via Apify jika tombol ditekan"""
    items, error = run_actual_scraping()
    if error:
        return jsonify({"status": "error", "message": error}), 500

    trend_results = process_hashtag_trends(items)
    return jsonify({
        "status": "success",
        "source": "live_apify",
        "data": trend_results
    })

@app.route('/api/posts/<hashtag>', methods=['GET'])
def get_posts_by_hashtag(hashtag):
    """Mendapatkan daftar postingan yang mengandung hashtag tertentu"""
    if not os.path.exists(LOCAL_JSON_DATASET):
        return jsonify({"status": "error", "message": "File JSON dataset tidak ditemukan."}), 404
        
    try:
        with open(LOCAL_JSON_DATASET, 'r', encoding='utf-8') as f:
            posts_data = json.load(f)
        
        hashtag_lower = hashtag.lower().strip()
        matched_posts = []
        for post in posts_data:
            tags = post.get('hashtags', [])
            if isinstance(tags, list):
                if any(t.lower().strip() == hashtag_lower for t in tags if isinstance(t, str)):
                    matched_posts.append(post)
                    
        return jsonify({
            "status": "success",
            "hashtag": hashtag,
            "data": matched_posts
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)