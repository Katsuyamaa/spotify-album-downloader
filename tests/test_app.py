import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_index_returns_200(client):
    response = client.get("/")
    assert response.status_code == 200

def test_index_contains_form(client):
    response = client.get("/")
    assert b"form" in response.data
    assert b"url" in response.data

import os
from unittest.mock import patch, MagicMock
import zipfile
from io import BytesIO

def test_download_missing_url_returns_400(client):
    response = client.post("/download", data={})
    assert response.status_code == 400

def test_download_invalid_url_returns_400(client):
    response = client.post("/download", data={"url": "not-a-spotify-url"})
    assert response.status_code == 400

def test_download_returns_zip_on_success(client, tmp_path):
    # Simulate spotdl creating an mp3 file in the temp dir
    def fake_run(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        # Write a fake mp3 into the output dir (last arg in cmd is the dir)
        out_dir = cmd[cmd.index("--output") + 1]
        fake_mp3 = os.path.join(out_dir, "track1.mp3")
        with open(fake_mp3, "wb") as f:
            f.write(b"fakemp3data")
        return result

    with patch("app.subprocess.run", side_effect=fake_run):
        response = client.post(
            "/download",
            data={"url": "https://open.spotify.com/album/abc123"}
        )

    assert response.status_code == 200
    assert response.content_type == "application/zip"
    zip_bytes = BytesIO(response.data)
    with zipfile.ZipFile(zip_bytes) as zf:
        assert "track1.mp3" in zf.namelist()

def test_download_spotdl_failure_returns_400(client):
    def fake_run_fail(cmd, **kwargs):
        result = MagicMock()
        result.returncode = 1
        result.stderr = "spotdl error: album not found"
        return result

    with patch("app.subprocess.run", side_effect=fake_run_fail):
        response = client.post(
            "/download",
            data={"url": "https://open.spotify.com/album/abc123"}
        )

    assert response.status_code == 400
