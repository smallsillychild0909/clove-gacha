"""圖片儲存：
- 設定 SUPABASE_URL + SUPABASE_SERVICE_KEY → 上傳到 Supabase Storage（永久保存），回傳完整公開網址
- 沒設定 → 存本地 uploads/（本地測試用），回傳 /uploads/xxx
"""
import os
import urllib.request
import urllib.error
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "uploads")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_BYTES = 5 * 1024 * 1024  # 5MB


def _headers(content_type):
    h = {"apikey": SUPABASE_SERVICE_KEY, "Content-Type": content_type, "x-upsert": "false"}
    # 舊版 service_role 金鑰（eyJ 開頭的 JWT）要放 Authorization；新版 sb_secret_ 金鑰只放 apikey
    if SUPABASE_SERVICE_KEY.startswith("eyJ"):
        h["Authorization"] = f"Bearer {SUPABASE_SERVICE_KEY}"
    return h


def save_image(upload, prefix: str) -> str:
    from fastapi import HTTPException

    ext = (Path(upload.filename).suffix or ".jpg").lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "只接受 jpg / png / gif / webp 圖片")
    data = upload.file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "圖片不可超過 5MB")
    filename = f"{prefix}_{uuid.uuid4().hex}{ext}"

    if not USE_SUPABASE:
        (UPLOAD_DIR / filename).write_bytes(data)
        return f"/uploads/{filename}"

    content_type = upload.content_type or "image/jpeg"
    req = urllib.request.Request(
        f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}",
        data=data,
        method="POST",
        headers=_headers(content_type),
    )
    try:
        with urllib.request.urlopen(req, timeout=30):
            pass
    except urllib.error.HTTPError as e:
        raise HTTPException(500, f"圖片上傳到 Supabase 失敗：{e.code} {e.read().decode(errors='ignore')}")
    return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{filename}"
