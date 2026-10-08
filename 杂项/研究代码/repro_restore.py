import json
import os
import tempfile
from pathlib import Path

tmp = Path(tempfile.mkdtemp(prefix="milk-restore-repro-"))
os.environ["MILK_DATA_DIR"] = str(tmp)
print("data_dir =", tmp)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

with TestClient(app) as client:
    token = client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "admin123"}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/api/v1/operations/backups", headers=headers)
    print("backup status:", r.status_code)
    backups = client.get("/api/v1/operations/backups", headers=headers).json()
    name = Path(backups[0]["file_path"]).name
    print("backup file:", name)

    r2 = client.post(
        "/api/v1/operations/restore", headers=headers, json={"file_name": name}
    )
    print("restore status:", r2.status_code)
    print("restore detail:", json.dumps(r2.json(), ensure_ascii=False)[:3000])
