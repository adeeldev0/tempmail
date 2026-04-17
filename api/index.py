from flask import Flask, jsonify, request
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import string
import time

app = Flask(__name__)

# Retry setup for better connection handling
def get_session():
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1.5, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def random_string(length=12):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

@app.route('/generate', methods=['GET'])
def generate_random_email():
    session = get_session()
    try:
        # Get domains
        domains_resp = session.get("https://api.mail.tm/domains", timeout=20)
        domains_resp.raise_for_status()
        domains = [item['domain'] for item in domains_resp.json().get('hydra:member', [])]

        if not domains:
            return jsonify({"error": "No domains available right now. Try again later or use VPN."}), 503

        domain = random.choice(domains)
        username = random_string(12)
        email = f"{username}@{domain}"
        password = random_string(16)

        # Create account
        create_resp = session.post(
            "https://api.mail.tm/accounts",
            json={"address": email, "password": password},
            timeout=15
        )
        
        if create_resp.status_code != 201:
            return jsonify({"error": "Account creation failed", "details": create_resp.text}), 400

        # Get token
        token_resp = session.post(
            "https://api.mail.tm/token",
            json={"address": email, "password": password},
            timeout=15
        )
        token = token_resp.json().get("token")

        if not token:
            return jsonify({"error": "Failed to get token"}), 400

        return jsonify({
            "status": "success",
            "email": email,
            "password": password,
            "token": token,
            "message": "Email ready! Use it for signup on any site.",
            "created_by": "Muhammad Adeel Baloch",
            "location": "Pakistan",
            "note": "This is a temporary mail API"
        })

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Connection failed to mail.tm server. Try using VPN."}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again later."}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/messages/<token>', methods=['GET'])
def get_messages(token):
    session = get_session()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = session.get("https://api.mail.tm/messages", headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        return jsonify({
            "status": "success",
            "total": data.get("hydra:totalItems", 0),
            "messages": data.get("hydra:member", []),
            "created_by": "Muhammad Adeel Baloch"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Optional: Root route for info
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Temp Mail API is running",
        "endpoints": {
            "generate": "/generate",
            "messages": "/messages/YOUR_TOKEN"
        },
        "created_by": "Muhammad Adeel Baloch - Pakistan    })
