import os
import shutil
import subprocess
import tempfile
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, send_file, make_response

app = Flask(__name__)

SPOTIFY_URL_PREFIX = "https://open.spotify.com/"
SPOTDL_FFMPEG = os.path.join(os.path.expanduser("~"), ".spotdl", "ffmpeg.exe")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url", "").strip()

    if not url or not url.startswith(SPOTIFY_URL_PREFIX):
        return make_response("Geçerli bir Spotify linki girin (şarkı, albüm veya liste).", 400)

    tmpdir = tempfile.mkdtemp(prefix="spotify_")
    try:
        cmd = [
            "spotdl", url,
            "--output", tmpdir,
            "--audio", "youtube", "soundcloud",
            "--ffmpeg", SPOTDL_FFMPEG,
            "--no-cache",
            "--dont-filter-results",
        ]
        if SPOTIFY_CLIENT_ID:
            cmd += ["--client-id", SPOTIFY_CLIENT_ID]
        if SPOTIFY_CLIENT_SECRET:
            cmd += ["--client-secret", SPOTIFY_CLIENT_SECRET]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            return make_response("İndirme zaman aşımına uğradı (10 dk). Liste çok büyük olabilir.", 400)

        if result.returncode != 0:
            error_detail = (result.stderr or result.stdout or "Bilinmeyen hata").strip()
            app.logger.error("spotdl failed: %s", error_detail)
            return make_response(f"İndirme başarısız:\n{error_detail}", 400)

        mp3_files = [f for f in os.listdir(tmpdir) if os.path.isfile(os.path.join(tmpdir, f))]
        if not mp3_files:
            return make_response("İndirilecek şarkı bulunamadı.", 400)

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for filename in mp3_files:
                zf.write(os.path.join(tmpdir, filename), filename)
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
    from dotenv import load_dotenv
    load_dotenv()
    app.run(debug=True)
