from flask import Flask, render_template, request,jsonify
import requests, random, base64, hashlib
from cryptography.fernet import Fernet
from pymongo import MongoClient
import os

app = Flask(__name__)

# ================= Mongo URL Decryption ================= #

def generate_key(password: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def decode_mongo_url_from_web(password: str, url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    encrypted_data = response.content
    key = generate_key(password)
    fernet = Fernet(key)
    decrypted_data = fernet.decrypt(encrypted_data)
    return decrypted_data.decode()

# ================= Load Remote URL from Mongo ================= #

def get_remote_url_from_mongo():
    try:
        password = "mongodbMac02335!"
        secret_url = "https://raw.githubusercontent.com/7b809/the_keys/refs/heads/main/tokentext.txt"
        mongo_uri = decode_mongo_url_from_web(password, secret_url)

        client = MongoClient(mongo_uri)
        db = client['F-CINEMA']
        doc = db.urls_data.find_one({'file_num': 1})
        if doc and 'public_url' in doc:
            return doc['public_url'].replace("/home", "")  # clean the `/home` part
    except Exception as e:
        print(f"❌ Failed to load REMOTE_URL from MongoDB: {e}")
    
    return None  # fallback

# ================= Dynamic REMOTE_URL ================= #
REMOTE_URL = get_remote_url_from_mongo() or "http://localhost:5000"  # fallback

# ================= Routes ================= #

@app.route('/')
def index():
    try:
        response = requests.get(f'{REMOTE_URL}/home')
        response.raise_for_status()
        json_data = response.json()

        message = json_data.get('message', 'No message')
        ip = json_data.get('ip_address', 'N/A')
        data = json_data.get('data', [])
        random.shuffle(data)
    except Exception as e:
        message = "Failed to fetch data"
        ip = "N/A"
        data = []
        print(f"❌ Error: {e}")

    return render_template("index.html", message=message, ip=ip, data=data,remote_url=REMOTE_URL)

@app.route('/play_video_page')
def play_video_page():
    video_url = request.args.get('url')
    ip_address = request.args.get('ip', 'N/A')
    title = request.args.get('title', 'Unknown')
    message = "Playing video directly from client link"

    return render_template("video.html", title=title, video_url=video_url, ip=ip_address, message=message)

@app.route('/fetch_video_info/<title_slug>')
def fetch_video_info(title_slug):
    try:
        remote_url = REMOTE_URL  # If you're storing REMOTE_URL in MongoDB
        url = f"{remote_url}/video/{title_slug}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        temp_url = f"{remote_url}/videos/{title_slug}.mp4"
        video_url = data.get("video_url",temp_url)
        ip_address = data.get("ip_address", "N/A")

        return jsonify({
            "video_url": video_url,
            "ip_address": ip_address
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @app.route('/video/<title_slug>')
# def video_api(title_slug):
#     try:
#         url = f"{REMOTE_URL}/video/{title_slug}"
#         response = requests.get(url)
#         response.raise_for_status()
#         video_data = response.json()
#         print(video_data)
#         video_url = video_data.get('url')
#         ip_address = video_data.get('ip_address', 'N/A')

#         return jsonify({
#             "video_url": video_url,
#             "ip_address": ip_address
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
