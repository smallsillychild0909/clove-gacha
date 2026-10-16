import os
import json
import random
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from database import init_db, get_db
from storage import save_image, UPLOAD_DIR
from auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin, require_member
)

# 初始化
init_db()


app = FastAPI(title="Clove 抽卡平台 API", version="1.0.0")

# CORS：ALLOWED_ORIGINS 用逗號分隔，例如 https://your-app.vercel.app
_origins = [o.strip().rstrip("/") for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,  # 使用 Bearer token，不需要 cookie
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ==================== Schemas ====================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RechargeRequest(BaseModel):
    user_id: Optional[int] = None
    amount: int
    note: Optional[str] = None

class PoolCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    intro_type: str = "image"  # image / text
    cost_single: int = 100
    cost_ten: int = 900
    total_quantity: int

class CardCreate(BaseModel):
    name: str
    total_quantity: int
    original_probability: Optional[float] = None  # 若不填則自動依數量計算

class DrawRequest(BaseModel):
    pool_id: int
    draw_type: str  # single / ten

# ==================== Auth ====================

@app.post("/api/auth/register")
def register(req: RegisterRequest):
    if len(req.password) < 6:
        raise HTTPException(400, "密碼至少 6 位")
    conn = get_db()
    try:
        hashed = hash_password(req.password)
        cur = conn.execute(
            "INSERT INTO users (username, email, password_hash, role, points) VALUES (?, ?, ?, 'member', 0)",
            (req.username, req.email, hashed)
        )
        conn.commit()
        user_id = cur.lastrowid
        token = create_access_token({"sub": user_id, "role": "member"})
        return {"token": token, "user": {"id": user_id, "username": req.username, "role": "member", "points": 0}}
    except Exception as e:
        conn.rollback()
        if "UNIQUE" in str(e):
            raise HTTPException(400, "使用者名稱或 Email 已存在")
        raise HTTPException(500, str(e))
    finally:
        conn.close()

@app.post("/api/auth/login")
def login(req: LoginRequest):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (req.username,)).fetchone()
    conn.close()
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(401, "帳號或密碼錯誤")
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "points": user["points"]
        }
    }

@app.get("/api/auth/me")
def me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "points": user["points"]
    }

# ==================== 獎池 (公開 + 會員) ====================

@app.get("/api/pools")
def list_pools(active_only: bool = True):
    conn = get_db()
    if active_only:
        rows = conn.execute(
            "SELECT id, name, description, image_url, intro_type, cost_single, cost_ten, total_quantity, remaining_quantity, is_active FROM pools WHERE is_active = 1 ORDER BY id DESC"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT id, name, description, image_url, intro_type, cost_single, cost_ten, total_quantity, remaining_quantity, is_active FROM pools ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/pools/{pool_id}")
def get_pool(pool_id: int):
    conn = get_db()
    pool = conn.execute("SELECT * FROM pools WHERE id = ?", (pool_id,)).fetchone()
    if not pool:
        conn.close()
        raise HTTPException(404, "獎池不存在")
    cards = conn.execute(
        "SELECT id, name, image_url, total_quantity, remaining_quantity, original_probability FROM cards WHERE pool_id = ? ORDER BY id",
        (pool_id,)
    ).fetchall()
    conn.close()
    result = dict(pool)
    result["cards"] = [dict(c) for c in cards]
    return result

# ==================== 抽卡 ====================

def weighted_draw(cards: list) -> dict | None:
    """依剩餘數量加權隨機抽一張"""
    available = [c for c in cards if c["remaining_quantity"] > 0]
    if not available:
        return None
    weights = [c["remaining_quantity"] for c in available]
    chosen = random.choices(available, weights=weights, k=1)[0]
    return chosen

@app.post("/api/draw")
def draw_cards(req: DrawRequest, user: dict = Depends(require_member)):
    if req.draw_type not in ("single", "ten"):
        raise HTTPException(400, "draw_type 必須是 single 或 ten")

    conn = get_db()
    try:
        pool = conn.execute("SELECT * FROM pools WHERE id = ? AND is_active = 1", (req.pool_id,)).fetchone()
        if not pool:
            raise HTTPException(404, "獎池不存在或已關閉")

        cost = pool["cost_single"] if req.draw_type == "single" else pool["cost_ten"]
        count = 1 if req.draw_type == "single" else 10

        if user["points"] < cost:
            raise HTTPException(400, f"點數不足，需要 {cost} 點，目前只有 {user['points']} 點")

        if pool["remaining_quantity"] < count:
            raise HTTPException(400, f"獎池剩餘不足，只剩 {pool['remaining_quantity']} 張")

        cards = [dict(c) for c in conn.execute(
            "SELECT * FROM cards WHERE pool_id = ?", (req.pool_id,)
        ).fetchall()]

        results = []
        for _ in range(count):
            chosen = weighted_draw(cards)
            if not chosen:
                break
            # 更新剩餘
            conn.execute(
                "UPDATE cards SET remaining_quantity = remaining_quantity - 1 WHERE id = ?",
                (chosen["id"],)
            )
            for c in cards:
                if c["id"] == chosen["id"]:
                    c["remaining_quantity"] -= 1
                    break
            results.append({
                "card_id": chosen["id"],
                "name": chosen["name"],
                "image_url": chosen["image_url"]
            })

        actual_count = len(results)
        if actual_count == 0:
            raise HTTPException(400, "獎池已抽完")

        # 若實際抽到少於預期（理論不該發生），按比例扣點
        actual_cost = cost if actual_count == count else int(cost * actual_count / count)

        # 更新使用者點數
        new_points = user["points"] - actual_cost
        conn.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, user["id"]))

        # 更新獎池剩餘
        conn.execute(
            "UPDATE pools SET remaining_quantity = remaining_quantity - ? WHERE id = ?",
            (actual_count, req.pool_id)
        )

        # 寫入抽卡紀錄
        result_json = json.dumps(results, ensure_ascii=False)
        conn.execute(
            "INSERT INTO draw_records (user_id, pool_id, draw_type, cost_points, result_json) VALUES (?, ?, ?, ?, ?)",
            (user["id"], req.pool_id, req.draw_type, actual_cost, result_json)
        )

        # 寫入交易紀錄
        conn.execute(
            "INSERT INTO transactions (user_id, type, amount, balance_after, note) VALUES (?, 'draw', ?, ?, ?)",
            (user["id"], -actual_cost, new_points, f"{'單抽' if req.draw_type=='single' else '十連'} 獎池#{req.pool_id}")
        )

        conn.commit()
        return {
            "success": True,
            "results": results,
            "cost": actual_cost,
            "remaining_points": new_points,
            "draw_count": actual_count
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, str(e))
    finally:
        conn.close()

# ==================== 會員紀錄 ====================

@app.get("/api/my/draw-records")
def my_draw_records(user: dict = Depends(require_member), limit: int = 50):
    conn = get_db()
    rows = conn.execute("""
        SELECT dr.*, p.name as pool_name
        FROM draw_records dr
        LEFT JOIN pools p ON dr.pool_id = p.id
        WHERE dr.user_id = ?
        ORDER BY dr.id DESC LIMIT ?
    """, (user["id"], limit)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["results"] = json.loads(d.pop("result_json") or "[]")
        result.append(d)
    return result

@app.get("/api/my/transactions")
def my_transactions(user: dict = Depends(require_member), limit: int = 50):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user["id"], limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ==================== 會員自行儲值（模擬） ====================

@app.post("/api/recharge")
def member_recharge(req: RechargeRequest, user: dict = Depends(require_member)):
    if req.amount <= 0:
        raise HTTPException(400, "儲值金額必須大於 0")
    conn = get_db()
    new_points = user["points"] + req.amount
    conn.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, user["id"]))
    conn.execute(
        "INSERT INTO transactions (user_id, type, amount, balance_after, note) VALUES (?, 'recharge', ?, ?, ?)",
        (user["id"], req.amount, new_points, req.note or "會員自行儲值")
    )
    conn.commit()
    conn.close()
    return {"success": True, "new_points": new_points}

# ==================== 管理控台 ====================

@app.post("/api/admin/pools")
def admin_create_pool(
    name: str = Form(...),
    description: str = Form(""),
    intro_type: str = Form("image"),
    cost_single: int = Form(100),
    cost_ten: int = Form(900),
    total_quantity: int = Form(...),
    image: Optional[UploadFile] = File(None),
    admin: dict = Depends(require_admin)
):
    if total_quantity <= 0:
        raise HTTPException(400, "獎池總數量必須大於 0")

    image_url = None
    if image and image.filename:
        image_url = save_image(image, "pool")

    conn = get_db()
    cur = conn.execute(
        """INSERT INTO pools (name, description, image_url, intro_type, cost_single, cost_ten, total_quantity, remaining_quantity)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, description, image_url, intro_type, cost_single, cost_ten, total_quantity, total_quantity)
    )
    conn.commit()
    pool_id = cur.lastrowid
    conn.close()
    return {"id": pool_id, "message": "獎池建立成功"}

@app.put("/api/admin/pools/{pool_id}")
def admin_update_pool(
    pool_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    cost_single: Optional[int] = Form(None),
    cost_ten: Optional[int] = Form(None),
    is_active: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    admin: dict = Depends(require_admin)
):
    conn = get_db()
    pool = conn.execute("SELECT * FROM pools WHERE id = ?", (pool_id,)).fetchone()
    if not pool:
        conn.close()
        raise HTTPException(404, "獎池不存在")

    updates = []
    params = []
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if cost_single is not None:
        updates.append("cost_single = ?")
        params.append(cost_single)
    if cost_ten is not None:
        updates.append("cost_ten = ?")
        params.append(cost_ten)
    if is_active is not None:
        updates.append("is_active = ?")
        params.append(is_active)
    if image and image.filename:
        image_url = save_image(image, "pool")
        updates.append("image_url = ?")
        params.append(image_url)

    if updates:
        params.append(pool_id)
        conn.execute(f"UPDATE pools SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()
    return {"message": "更新成功"}

@app.post("/api/admin/pools/{pool_id}/cards")
def admin_add_card(
    pool_id: int,
    name: str = Form(...),
    total_quantity: int = Form(...),
    original_probability: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    admin: dict = Depends(require_admin)
):
    if total_quantity <= 0:
        raise HTTPException(400, "卡面數量必須大於 0")

    conn = get_db()
    pool = conn.execute("SELECT * FROM pools WHERE id = ?", (pool_id,)).fetchone()
    if not pool:
        conn.close()
        raise HTTPException(404, "獎池不存在")

    # 檢查總卡面數量不超過獎池總量
    current_sum = conn.execute(
        "SELECT COALESCE(SUM(total_quantity), 0) as s FROM cards WHERE pool_id = ?", (pool_id,)
    ).fetchone()["s"]
    if current_sum + total_quantity > pool["total_quantity"]:
        conn.close()
        raise HTTPException(400, f"卡面總數將超過獎池上限（目前已設定 {current_sum}，上限 {pool['total_quantity']}）")

    image_url = None
    if image and image.filename:
        image_url = save_image(image, "card")

    # 若未指定概率，依數量佔總量比例計算
    prob = original_probability
    if prob is None:
        prob = total_quantity / pool["total_quantity"] if pool["total_quantity"] > 0 else 0

    cur = conn.execute(
        """INSERT INTO cards (pool_id, name, image_url, total_quantity, remaining_quantity, original_probability)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (pool_id, name, image_url, total_quantity, total_quantity, prob)
    )
    conn.commit()
    card_id = cur.lastrowid
    conn.close()
    return {"id": card_id, "message": "卡面新增成功"}

@app.get("/api/admin/pools/{pool_id}/cards")
def admin_list_cards(pool_id: int, admin: dict = Depends(require_admin)):
    conn = get_db()
    pool = conn.execute("SELECT * FROM pools WHERE id = ?", (pool_id,)).fetchone()
    if not pool:
        conn.close()
        raise HTTPException(404, "獎池不存在")
    cards = conn.execute(
        "SELECT id, name, image_url, total_quantity, remaining_quantity, original_probability FROM cards WHERE pool_id = ? ORDER BY id",
        (pool_id,)
    ).fetchall()
    conn.close()
    return {
        "pool": dict(pool),
        "cards": [dict(c) for c in cards]
    }

@app.post("/api/admin/recharge")
def admin_recharge(req: RechargeRequest, admin: dict = Depends(require_admin)):
    if not req.user_id:
        raise HTTPException(400, "請指定 user_id")
    if req.amount == 0:
        raise HTTPException(400, "金額不可為 0")

    conn = get_db()
    target = conn.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(404, "使用者不存在")

    new_points = target["points"] + req.amount
    if new_points < 0:
        conn.close()
        raise HTTPException(400, "扣點後點數不可為負")

    tx_type = "admin_recharge" if req.amount > 0 else "admin_deduct"
    conn.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, req.user_id))
    conn.execute(
        "INSERT INTO transactions (user_id, type, amount, balance_after, note, operator_id) VALUES (?, ?, ?, ?, ?, ?)",
        (req.user_id, tx_type, req.amount, new_points, req.note or "管理員手動操作", admin["id"])
    )
    conn.commit()
    conn.close()
    return {"success": True, "new_points": new_points}

@app.post("/api/admin/test-recharge")
def admin_test_recharge(req: RechargeRequest, admin: dict = Depends(require_admin)):
    """系統測試儲值：給指定使用者加點"""
    if not req.user_id:
        raise HTTPException(400, "請指定 user_id")
    if req.amount <= 0:
        raise HTTPException(400, "測試儲值金額必須大於 0")

    conn = get_db()
    target = conn.execute("SELECT * FROM users WHERE id = ?", (req.user_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(404, "使用者不存在")

    new_points = target["points"] + req.amount
    conn.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, req.user_id))
    conn.execute(
        "INSERT INTO transactions (user_id, type, amount, balance_after, note, operator_id) VALUES (?, 'test_recharge', ?, ?, ?, ?)",
        (req.user_id, req.amount, new_points, req.note or "系統測試儲值", admin["id"])
    )
    conn.commit()
    conn.close()
    return {"success": True, "new_points": new_points}

@app.get("/api/admin/users")
def admin_list_users(admin: dict = Depends(require_admin)):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, email, role, points, created_at FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/admin/transactions")
def admin_transactions(
    user_id: Optional[int] = None,
    limit: int = 100,
    admin: dict = Depends(require_admin)
):
    conn = get_db()
    if user_id:
        rows = conn.execute(
            "SELECT t.*, u.username FROM transactions t LEFT JOIN users u ON t.user_id = u.id WHERE t.user_id = ? ORDER BY t.id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT t.*, u.username FROM transactions t LEFT JOIN users u ON t.user_id = u.id ORDER BY t.id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/admin/draw-records")
def admin_draw_records(limit: int = 100, admin: dict = Depends(require_admin)):
    conn = get_db()
    rows = conn.execute("""
        SELECT dr.*, u.username, p.name as pool_name
        FROM draw_records dr
        LEFT JOIN users u ON dr.user_id = u.id
        LEFT JOIN pools p ON dr.pool_id = p.id
        ORDER BY dr.id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["results"] = json.loads(d.pop("result_json") or "[]")
        result.append(d)
    return result

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/")
def root():
    return {"message": "Clove 抽卡平台 API 運行中", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
