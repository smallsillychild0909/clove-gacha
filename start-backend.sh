#!/bin/bash
set -e
cd "$(dirname "$0")/backend"
export PATH="$HOME/.local/bin:$PATH"

echo "=== 啟動 Clove 後端 API ==="
echo "位址: http://127.0.0.1:8000"
echo "API 文件: http://127.0.0.1:8000/docs"
echo ""

# 確保套件存在
python3 -c "import fastapi, uvicorn, multipart" 2>/dev/null || {
  echo "正在安裝 Python 套件..."
  pip3 install -r requirements.txt --user -q
}

python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
