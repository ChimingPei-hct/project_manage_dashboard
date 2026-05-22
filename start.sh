#!/usr/bin/env bash
# 项目根入口:转发到 app/start.sh
exec "$(dirname "$0")/app/start.sh" "$@"
