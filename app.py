import os
import subprocess
import tempfile
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
