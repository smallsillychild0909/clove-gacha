#!/bin/bash
set -e
cd "$(dirname "$0")/frontend"

echo "=== 啟動 Clove 前端 ==="
echo "位址: http://127.0.0.1:5173"
echo ""

if [ ! -d node_modules ] || [ ! -d node_modules/react-router-dom ]; then
  echo "正在安裝前端套件 (npm install)..."
  npm install
fi

npm run dev -- --host 127.0.0.1 --port 5173
