# 部署版修改說明

- 後端：`DATABASE_URL` 有設定 → Supabase Postgres；沒設定 → 本地 SQLite（`backend/clove.db`）
- 圖片：`SUPABASE_URL` + `SUPABASE_SERVICE_KEY` 有設定 → Supabase Storage；沒設定 → 本地 `uploads/`
- 前端：`VITE_API_URL` 設定後端網址；本地留空走 Vite proxy
- 設定範例見 `backend/.env.example`、`frontend/.env.example`
- 完整教學見 `部署教學.md`

本地測試方式和原本一樣（start-backend.sh / start-frontend.sh），不用設定任何環境變數。
