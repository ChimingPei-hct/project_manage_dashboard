#!/usr/bin/env bash
# 本地开发启动:并行起后端 (18080) + 前端 dev server (15173)
# 默认启用 Dev 后门(DEV_LOGIN=1)
# DATA_DIR 未设时回退到仓库内 ../design

set -euo pipefail

cd "$(dirname "$0")"

export DEV_LOGIN="${DEV_LOGIN:-1}"
export DATA_DIR="${DATA_DIR:-$(cd .. && pwd)/design}"
export PORT="${PORT:-18080}"

echo "[start] DATA_DIR=${DATA_DIR}"
echo "[start] DEV_LOGIN=${DEV_LOGIN}"

# 后端
(
  cd backend
  if [[ ! -d .venv ]]; then
    echo "[start] backend .venv missing, run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt" >&2
    exit 1
  fi
  source .venv/bin/activate
  exec uvicorn main:app --host 0.0.0.0 --port "${PORT}" --reload
) > backend.log 2>&1 &
BACK_PID=$!
echo "$BACK_PID" > backend/.backend.pid
echo "[start] backend pid=$BACK_PID (log: app/backend.log)"

# 前端
(
  cd frontend
  if [[ ! -d node_modules ]]; then
    echo "[start] frontend node_modules missing, run: cd app/frontend && npm install" >&2
    exit 1
  fi
  exec npm run dev
) > frontend.log 2>&1 &
FRONT_PID=$!
echo "$FRONT_PID" > frontend/.frontend.pid
echo "[start] frontend pid=$FRONT_PID (log: app/frontend.log)"

cleanup() {
  echo "[start] shutting down..."
  kill "$BACK_PID" "$FRONT_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "[start] open http://localhost:15173/?view=pdt"
wait
