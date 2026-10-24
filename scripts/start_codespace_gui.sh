#!/usr/bin/env bash
set -euo pipefail

display_number=:1
app_pid=""
window_manager_pid=""
vnc_pid=""
xvfb_pid=""

cleanup() {
    for process_id in "$app_pid" "$window_manager_pid" "$vnc_pid" "$xvfb_pid"; do
        if [[ -n "$process_id" ]]; then
            kill "$process_id" 2>/dev/null || true
        fi
    done
}

trap cleanup EXIT INT TERM

Xvfb "$display_number" -screen 0 1440x900x24 -nolisten tcp -ac >/tmp/spms-xvfb.log 2>&1 &
xvfb_pid=$!
export DISPLAY="$display_number"

fluxbox >/tmp/spms-fluxbox.log 2>&1 &
window_manager_pid=$!
x11vnc -display "$display_number" -auth /dev/null -localhost -nopw -forever -shared -rfbport 5900 >/tmp/spms-x11vnc.log 2>&1 &
vnc_pid=$!
python main.py &
app_pid=$!

websockify --web=/usr/share/novnc 127.0.0.1:6080 localhost:5900