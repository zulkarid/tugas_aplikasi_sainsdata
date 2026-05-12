import os
import json
import pandas as pd
import xml.etree.ElementTree as ET
from flask import Flask, render_template, jsonify
from datetime import datetime
from collections import Counter
from apify_client import ApifyClient

app = Flask(__name__)

# Lokasi folder hasil
OUTPUT_FOLDER = 'scraped_data_results'
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_apify_token():
    try:
        tree = ET.parse('config.xml')
        root = tree.getroot()
        return root.find('apify/api_token').text
    except Exception as e:
        print(f"Error XML: {e}")
        return None

def run_actual_scraping(): #menghubungkan api dari apify
    token = get_apify_token()
    if not token:
        return None, "Token tidak valid"

    client = ApifyClient(token)

    try:
        run_input = {
            "hashtags": ["fyp"],
            "resultsLimit": 20,
        }
        
        # Memulai task di server Apify
        run = client.actor("apify/instagram-hashtag-scraper").call(run_input=run_input)
        
        # Mengambil hasil dari dataset Apify
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        # Konversi ke Dataframe untuk diproses
        df = pd.DataFrame(items)
        
        # Menyimpan hasil ke lokal sebagai arsip CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"apify_result_{timestamp}.csv"
        save_path = os.path.join(OUTPUT_FOLDER, filename)
        df.to_csv(save_path, index=False)
        
        return df, None
    except Exception as e:
        return None, str(e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scrape', methods=['POST'])
def handle_scrape(): #jalankan scraping
    df, error = run_actual_scraping()
    
    if error:
        return jsonify({"status": "error", "message": error}), 500

    # ]analisa trend dengan menghitung frekuensi hashtag
    all_hashtags = []
    # asumsi semua kolom berisi hashtag
    for col in df.columns:
        if 'hashtags' in col:
            all_hashtags.extend(df[col].dropna().tolist())
    
    top_10 = Counter(all_hashtags).most_common(10)
    trend_results = [{"hashtag": h, "count": c} for h, c in top_10]

    return jsonify({
        "status": "success",
        "data": trend_results
    })

if __name__ == '__main__': #flask
    app.run(debug=True, host='0.0.0.0')