import os
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, send_file, make_response

app = Flask(__name__)

SPOTIFY_URL_PREFIX = "https://open.spotify.com/"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()

    if not url or not url.startswith(SPOTIFY_URL_PREFIX):
        return make_response("Geçerli bir Spotify albüm linki girin.", 400)

    tmpdir = tempfile.mkdtemp(prefix="spotify_")
    try:
        result = subprocess.run(
            ["spotdl", url, "--output", tmpdir],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            app.logger.error("spotdl failed: %s", result.stderr)
            return make_response("İndirme başarısız oldu. Lütfen geçerli bir Spotify albüm linki girdiğinizden emin olun.", 400)

        if not os.listdir(tmpdir):
            return make_response("İndirilecek şarkı bulunamadı.", 400)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename in os.listdir(tmpdir):
                filepath = os.path.join(tmpdir, filename)
                if os.path.isfile(filepath):
                    zf.write(filepath, filename)
        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype="application/zip",
            as_attachment=True,
            download_name="album.zip",
        )
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    app.run(debug=True)
