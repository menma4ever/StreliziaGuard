import os
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def index():
    return "Alive"

def run():
    port = int(os.environ.get("PORT", 8080))  # use Render's port if set, default to 8080 locally
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
