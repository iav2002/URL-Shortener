import os
import string
import random
from flask import Flask, jsonify, request, redirect
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Supabase connection
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def generate_code(length=6):
    """Generate a random alphanumeric short code."""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


@app.route("/api/health")
def health():
    """Quick check that Flask + Supabase are connected."""
    try:
        result = supabase.table("urls").select("id").limit(1).execute()
        return jsonify({"status": "ok", "db": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500


@app.route("/api/shorten", methods=["POST"])
def shorten():
    """Take a long URL, generate a short code, store it."""
    data = request.get_json()

    if not data or not data.get("url"):
        return jsonify({"error": "Missing 'url' field"}), 400

    original_url = data["url"]

    if not original_url.startswith(("http://", "https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    # Check for duplicate
    existing = supabase.table("urls") \
        .select("short_code") \
        .eq("original_url", original_url) \
        .execute()

    if existing.data:
        code = existing.data[0]["short_code"]
        short_url = f"{request.host_url}{code}"
        return jsonify({
            "short_url": short_url,
            "short_code": code,
            "reused": True
        }), 200

    # Generate unique code
    code = generate_code()

    try:
        supabase.table("urls").insert({
            "short_code": code,
            "original_url": original_url
        }).execute()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    short_url = f"{request.host_url}{code}"

    return jsonify({
        "short_url": short_url,
        "short_code": code,
        "reused": False
    }), 201

if __name__ == "__main__":
    app.run(debug=True, port=5001)