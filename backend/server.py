from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import base64
import os

# Serve index.html from the parent directory
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..'), static_url_path='')
CORS(app)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
print("TOKEN:", GITHUB_TOKEN)
REPO = "atharvawagh96k/rcpit-papers"
BRANCH = "main"

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/ping")
def ping():
    return jsonify({"status": "server is alive", "token_set": bool(GITHUB_TOKEN)})

@app.route("/upload", methods=["POST", "GET"])
def upload():

    # Test endpoint
    if request.method == "GET":
        return jsonify({"message": "Upload API is working"})

    file = request.files.get("file")
    filename = request.form.get("filename")

    print(f"[UPLOAD] filename={filename}, file={file}")

    if not file or not filename:
        return jsonify({"error": "Missing file or filename"}), 400

    content = base64.b64encode(file.read()).decode()

    url = f"https://api.github.com/repos/{REPO}/contents/papers/{filename}"

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

    print("[UPLOAD] GitHub response:", r.status_code)
    print("[UPLOAD] GitHub body:", r.text)

    # File created successfully
    if r.status_code in [200, 201]:
        return jsonify({"status": "ok"})

    # File already exists → update it
    elif r.status_code == 422:
        get_r = requests.get(url, headers=headers)

        if get_r.status_code == 200:
            sha = get_r.json().get("sha")
            data["sha"] = sha

            r2 = requests.put(url, headers=headers, json=data)

            if r2.status_code in [200, 201]:
                return jsonify({"status": "ok"})

        return jsonify({"error": "Failed to update existing file"}), 500

    else:
        return jsonify({"error": r.text}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
