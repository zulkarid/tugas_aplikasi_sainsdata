import json
from collections import Counter

def generate_trend_data(instagram_results):
    # Mengambil semua hashtag dari kolom hashtags/0 sampai hashtags/29
    all_hashtags = []
    for post in instagram_results:
        for i in range(30):
            tag = post.get(f'hashtags/{i}')
            if pd.notna(tag): # Pastikan bukan data kosong (NaN)
                all_hashtags.append(tag)
    
    # Hitung 10 hashtag terbanyak
    counts = Counter(all_hashtags).most_common(10)
    
    # Simpan ke file JSON agar bisa dibaca JavaScript
    trend_data = [{"hashtag": h, "count": c} for h, c in counts]
    
    with open('top_hashtags.json', 'w') as f:
        json.dump(trend_data, f)
    
    print("[System] Trend data updated in top_hashtags.json")

# Panggil fungsi ini setelah kamu mendapatkan instagram_results
generate_trend_data(instagram_results)