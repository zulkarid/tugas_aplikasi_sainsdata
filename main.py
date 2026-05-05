import requests
import json
import random
from pprint import pprint

# 1. Gunakan nama plural agar tidak bentrok dengan item loop
usernames = ["jio", "beyonce", "shakira", "katyperry"]
proxy = "http://username:password@PROXY_SERVER:PORT"
output = {}

def get_headers(username):
    headers = {
        "authority": "www.instagram.com",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-language": "en-GB, en-US;q=0.9,en;q=0.8",
        "upgrade-insecure-requests": "1",
        "connection": "close", # Tanda koma ditambahkan
        "user-agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/111.0.0.0 Safari/537.36"
        ])
    }
    return headers

def parse_data(username_key, user_data):
    captions = []
    # Perbaikan typo: 'edge_owner_to_timeline_media'
    media = user_data.get('edge_owner_to_timeline_media', {})
    edges = media.get('edges', [])

    if len(edges) > 0:
        for node in edges:
            inner_node = node['node']
            caption_edges = inner_node.get('edge_media_to_caption', {}).get('edges', [])
            
            if len(caption_edges) > 0:
                text = caption_edges[0]['node']['text']
                captions.append(text)

    # Perbaikan key: 'edge_followed_by' dan 'full_name'
    output[username_key] = {
        "name": user_data.get("full_name"),
        "category": user_data.get("category_name"),
        "followers": user_data.get("edge_followed_by", {}).get("count"),
        "posts": captions,
    }

def main():
    for user in usernames: # Nama variabel tidak bentrok lagi
        print(f"Memproses: {user}...")
        url = f"https://instagram.com/{user}/?__a=1&__d=dis"
        
        try:
            # Note: Gunakan proxy yang valid atau hapus parameter proxies jika tidak pakai
            response = requests.get(url, headers=get_headers(user), timeout=10)
            
            if response.status_code == 200:
                res_json = response.json() # Lebih simpel daripada json.loads(response.text)
                
                # Instagram struktur datanya: res_json['graphql']['user']
                if "graphql" in res_json:
                    user_info = res_json["graphql"]["user"]
                    parse_data(user, user_info)
                else:
                    print(f"Struktur JSON tidak sesuai untuk {user}")

            elif response.status_code in [301, 302]:
                print(f"Gagal: Terkena redirect ke login untuk {user}")
            else:
                print(f"Request gagal. Status: {response.status_code}")
                
        except Exception as e:
            print(f"Error saat memproses {user}: {e}")

if __name__ == "__main__":
    main()
    pprint(output)