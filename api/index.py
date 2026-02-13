import os
import string
import random
from flask import Flask, jsonify, request, redirect
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import time

load_dotenv()

app = Flask(__name__, static_folder='../public', static_url_path='')

# Supabase connection
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# Simple in-memory rate limiter
rate_limit = defaultdict(list)
RATE_LIMIT = 10        # max requests
RATE_WINDOW = 60       # per 60 seconds

@app.route("/")
def home():
    return app.send_static_file("index.html")


def is_rate_limited(ip):
    """Check if an IP has exceeded the request limit."""
    now = time.time()
    # Remove old timestamps outside the window
    rate_limit[ip] = [t for t in rate_limit[ip] if now - t < RATE_WINDOW]
    # Check limit
    if len(rate_limit[ip]) >= RATE_LIMIT:
        return True
    rate_limit[ip].append(now)
    return False



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

    # Rate limit check
    if is_rate_limited(request.remote_addr):
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429

    if not data or not data.get("url"):
        return jsonify({"error": "Missing 'url' field"}), 400

    original_url = data["url"]

    if not original_url.startswith(("http://", "https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    # Check for duplicate (skip if user wants a custom alias)
    if not data.get("custom_code"):
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

  # Custom alias or random code
    custom = data.get("custom_code")

    if custom:
        # Check if custom code is already taken
        taken = supabase.table("urls") \
            .select("short_code") \
            .eq("short_code", custom) \
            .execute()

        if taken.data:
            return jsonify({"error": "Custom code already taken"}), 409

        code = custom
    else:
        code = generate_code()


    # Build the row to insert
    row = {
        "short_code": code,
        "original_url": original_url
    }

    # Optional expiration
    expires_in = data.get("expires_in_days")
    if expires_in is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=int(expires_in))
        row["expires_at"] = expires_at.isoformat()


    try:
        supabase.table("urls").insert(row).execute()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

    short_url = f"{request.host_url}{code}"

    return jsonify({
        "short_url": short_url,
        "short_code": code,
        "reused": False
    }), 201


@app.route("/<code>")
def redirect_url(code):
    """Look up a short code and redirect to the original URL."""
    # Skip static files
    if '.' in code:
        return app.send_static_file(code)

    try:
        result = supabase.table("urls") \
            .select("original_url, expires_at") \
            .eq("short_code", code) \
            .single() \
            .execute()
    except Exception:
        return jsonify({"error": "Short code not found"}), 404

    # Check expiration
    expires_at = result.data.get("expires_at")
    if expires_at:
        exp_time = datetime.fromisoformat(expires_at)
        if datetime.now(timezone.utc) > exp_time:
            return jsonify({"error": "This link has expired"}), 410

    supabase.rpc("increment_clicks", {"code": code}).execute()

    return redirect(result.data["original_url"], 302)


@app.route("/api/stats/<code>")
def stats(code):
    """Return metadata about a short link."""
    try:
        result = supabase.table("urls") \
            .select("short_code, original_url, clicks, created_at, expires_at") \
            .eq("short_code", code) \
            .single() \
            .execute()
    except Exception:
        return jsonify({"error": "Short code not found"}), 404

    return jsonify(result.data), 200




if __name__ == "__main__":
    app.run(debug=True, port=5001)