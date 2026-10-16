# Clove 風格線上抽卡平台

完整功能的 Oripa / 抽卡網站，仿 Clove 風格。

## 技術棧

- **前端**：React (Vite) + React Router + Tailwind CSS (CDN)
- **後端**：Python FastAPI + SQLite
- **圖片**：本地 `uploads/` 資料夾
- **介面語言**：繁體中文

## 功能

### 會員端
- 註冊 / 登入
- 主頁顯示活動獎池（圖片、名稱、剩餘/總數）
- 獎池詳情、單抽 / 十連抽
- 儲值遊戲幣（模擬）
- 抽卡紀錄 + 消費紀錄

### 管理控台
- 獨立登入
- 新增活動卡池（圖片/文字介紹、單抽/十連費用、總數量）
- 卡池內新增卡面（上傳圖片、名稱、可抽出張數、原始概率）
- 檢視卡面池（名稱｜總數｜已抽出｜剩餘｜原始概率）
- 手動儲值 / 扣點 + 系統測試儲值
- 會員消費與抽卡紀錄查詢

## 快速啟動

### 1. 後端

```bash
cd backend
pip install -r requirements.txt
# 或：pip install fastapi uvicorn python-multipart pyjwt passlib bcrypt python-dotenv aiofiles

python main.py
# 預設跑在 http://localhost:8000
# API 文件：http://localhost:8000/docs
```

### 2. 前端

```bash
cd frontend
npm install
npm run dev
# 預設跑在 http://localhost:5173
```

### 預設帳號

| 角色   | 帳號  | 密碼     | 初始點數 |
|--------|-------|----------|----------|
| 管理員 | admin | admin123 | 0        |
| 測試會員 | user  | user123  | 10000    |

## 抽卡邏輯

- 獎池為**有限數量**，抽出後剩餘減少
- 機率依各卡面「剩餘張數」加權隨機
- 必須先設定獎池總數量，才能新增卡面
- 卡面總張數不可超過獎池總量

## 目錄結構

```
clove-gacha/
├── backend/
│   ├── main.py          # FastAPI 主程式
│   ├── database.py      # SQLite 初始化
│   ├── auth.py          # JWT 認證
│   ├── requirements.txt
│   └── clove.db         # 執行後自動產生
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── context/AuthContext.jsx
│   │   ├── components/Navbar.jsx
│   │   ├── pages/       # 會員頁面
│   │   └── pages/admin/ # 管理控台
│   └── package.json
└── uploads/             # 上傳圖片存放處
```

## 注意事項

- 正式環境請更換 `auth.py` 中的 `SECRET_KEY`
- 儲值目前為模擬，正式需串接金流
- 圖片上傳僅支援本地存檔
