#!/usr/bin/env bash
# 生产单实例启动:读 DATA_DIR/config.json 里的 port,起 uvicorn(无 --reload)
# 必填环境变量:DATA_DIR
# 可选:FEISHU_APP_SECRET、COOKIE_SECURE=1

set -euo pipefail

if [[ -z "${DATA_DIR:-}" ]]; then
  echo "[start-instance] DATA_DIR is required" >&2
  exit 1
fi

CONFIG="${DATA_DIR}/config.json"
if [[ ! -f "${CONFIG}" ]]; then
  echo "[start-instance] config.json not found at ${CONFIG}" >&2
  exit 1
fi

PORT=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('port', 18080))" "${CONFIG}")

cd "$(dirname "$0")"
exec ./.venv/bin/uvicorn main:app --host 0.0.0.0 --port "${PORT}"
