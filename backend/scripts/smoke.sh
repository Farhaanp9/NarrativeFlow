#!/usr/bin/env bash
# End-to-end smoke test against a running stack (docker compose up).
# Creates a simulation, pauses it, steps one tick, resumes it to the end,
# then checks the graph, an agent, the report and the frontend.
# Usage: backend/scripts/smoke.sh [backend_url] [frontend_url]
set -euo pipefail

API=${1:-http://localhost:8000}
WEB=${2:-http://localhost:3000}
N_AGENTS=300

get() { curl -fsS "$API$1"; }
post() { curl -fsS -X POST -H 'Content-Type: application/json' -d "${2:-}" "$API$1"; }
py() { python3 -c "import json, sys; d = json.load(sys.stdin); $1"; }
ticks() { get "/api/simulations/$ID" | py 'print(len(d["metrics_history"]))'; }
wait_for() {
  local s=""
  for _ in $(seq 300); do
    s=$(get "/api/simulations/$ID" | py 'print(d["status"])')
    [ "$s" = "$1" ] && return 0
    [ "$s" = completed ] || [ "$s" = failed ] && break
    sleep 0.2
  done
  echo "FAIL: expected status $1, got $s" >&2
  exit 1
}

get /api/health >/dev/null
curl -fsS "$WEB/api/health" >/dev/null  # the frontend proxies /api to the backend

ID=$(post /api/simulations "{\"seed_text\": \"Smoke test: miracle cure claim\",
  \"population_size\": $N_AGENTS, \"max_ticks\": 30, \"tick_speed\": 10}" | py 'print(d["id"])')
echo "simulation $ID"

wait_for running
post "/api/simulations/$ID/pause" >/dev/null
sleep 0.5
before=$(ticks)
post "/api/simulations/$ID/step" >/dev/null
sleep 0.5
after=$(ticks)
[ "$after" -eq $((before + 1)) ] || { echo "FAIL: step went $before -> $after" >&2; exit 1; }
post "/api/simulations/$ID/resume" >/dev/null
wait_for completed
echo "paused at tick $before, stepped to $after, completed"

get "/api/simulations/$ID/graph" | py "assert len(d['node_states']) == $N_AGENTS, 'node states'"
get "/api/simulations/$ID/agents/0" | py 'assert d["archetype_name"] != "Unknown", d'
get "/api/reports/$ID" | py 'assert len(d["content"]) > 100, "report too short"'
get "/api/reports/$ID/data" | py 'assert len(d["metrics_history"]) >= 30, "metrics"'
curl -fsS "$WEB/" >/dev/null
curl -fsS "$WEB/reports/$ID" | grep -q "Export JSON" || { echo "FAIL: report page" >&2; exit 1; }

curl -fsS -X DELETE "$API/api/simulations/$ID" >/dev/null
echo "smoke OK"
