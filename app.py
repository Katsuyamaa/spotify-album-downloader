import os
import subprocess
from dotenv import load_dotenv
from flask import Flask, render_template, request, Response, stream_with_context, make_response

load_dotenv()

app = Flask(__name__)

SPOTIFY_URL_PREFIX = "https://open.spotify.com/"
SPOTDL_FFMPEG = os.path.join(os.path.expanduser("~"), ".spotdl", "ffmpeg.exe")
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
DEFAULT_OUTPUT = os.path.join(os.path.expanduser("~"), "Music", "Spotify")

@app.route("/")
def index():
    return render_template("index.html", default_output=DEFAULT_OUTPUT)

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url", "").strip()
    output_dir = request.args.get("output_dir", DEFAULT_OUTPUT).strip() or DEFAULT_OUTPUT

    if not url or not url.startswith(SPOTIFY_URL_PREFIX):
        return make_response("Geçerli bir Spotify linki girin (şarkı, albüm veya liste).", 400)

    os.makedirs(output_dir, exist_ok=True)

    cmd = [
        "spotdl", url,
        "--output", os.path.join(output_dir, "{artists} - {title}.{output-ext}"),
        "--audio", "youtube", "soundcloud",
        "--ffmpeg", SPOTDL_FFMPEG,
        "--no-cache",
        "--dont-filter-results",
        "--threads", "1",
    ]
    if SPOTIFY_CLIENT_ID:
        cmd += ["--client-id", SPOTIFY_CLIENT_ID]
    if SPOTIFY_CLIENT_SECRET:
        cmd += ["--client-secret", SPOTIFY_CLIENT_SECRET]

    def generate():
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            for line in proc.stdout:
                line = line.strip()
                if line:
                    yield f"data: {line}\n\n"
            proc.wait()
            if proc.returncode == 0:
                yield f"data: ✅ Tamamlandı! Dosyalar: {output_dir}\n\n"
                yield "data: __DONE__\n\n"
            else:
                yield "data: ❌ Hata oluştu. Yukarıdaki çıktıya bakın.\n\n"
                yield "data: __DONE__\n\n"
        except Exception as e:
            yield f"data: ❌ Beklenmeyen hata: {e}\n\n"
            yield "data: __DONE__\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(debug=True)
