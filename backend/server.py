from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import base64
import os

load_dotenv()

# Serve index.html from the parent directory
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..'), static_url_path='')
CORS(app)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
print("TOKEN:", GITHUB_TOKEN)

REPO = "atharvawagh96k/rcpit-papers"
BRANCH = "main"

# LOGIN CREDENTIALS
STUDENT_USER = "student"
STUDENT_PASS = "1234"

ADMIN_USER = "rcpit_admin"
ADMIN_PASS = "rcpit@2001"


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/ping")
def ping():
    return jsonify({"status": "server is alive", "token_set": bool(GITHUB_TOKEN)})


@app.route("/upload", methods=["POST"])
def upload():

    file = request.files.get("file")
    filename = request.form.get("filename")

    print(f"[UPLOAD] filename={filename}, file={file}")

    if not file or not filename:
        return jsonify({"error": "Missing file or filename"}), 400

    content = base64.b64encode(file.read()).decode()

    url = f"https://api.github.com/repos/{REPO}/contents/papers/{filename}"
    print(f"[UPLOAD] Pushing to: {url}")

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "message": f"Upload {filename}",
        "content": content,
        "branch": BRANCH
    }

    r = requests.put(url, headers=headers, json=data)

    print(f"[UPLOAD] GitHub response: {r.status_code}")
    print(f"[UPLOAD] GitHub body: {r.text[:500]}")

    if r.status_code in [200, 201]:
        return jsonify({"status": "ok"})

    elif r.status_code == 422:
        # File exists → update
        get_r = requests.get(url, headers=headers)

        if get_r.status_code == 200:
            sha = get_r.json().get("sha")
            data["sha"] = sha

            r2 = requests.put(url, headers=headers, json=data)

            if r2.status_code in [200, 201]:
                return jsonify({"status": "ok"})

        return jsonify({"error": r.text}), 500

    else:
        return jsonify({"error": r.text}), 500


@app.route("/login", methods=["POST"])
def login():

    data = request.json

    username = data.get("username")
    password = data.get("password")
    role = data.get("role")

    # Student login
    if role == "student":
        if username == STUDENT_USER and password == STUDENT_PASS:
            return jsonify({"status": "ok", "role": "student"})
        else:
            return jsonify({"status": "fail"}), 401

    # Admin login
    elif role == "admin":
        if username == ADMIN_USER and password == ADMIN_PASS:
            return jsonify({"status": "ok", "role": "admin"})
        else:
            return jsonify({"status": "fail"}), 401

    return jsonify({"status": "fail"}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
