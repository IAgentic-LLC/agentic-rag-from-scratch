#!/bin/bash
# bash run_baselines.sh   Indexes the grown corpus, then records the baselines (4 judged runs each). Keys are read from product/backend/.env, never printed.
cd "$(dirname "$0")"
set -a; . ../backend/.env; set +a
export PYTHONUTF8=1 JUDGE_MODEL=deepseek:deepseek-flash
export DOCS_DIR="$(pwd -W)/data/docs" INDEX_PATH="$(pwd -W)/data/index_v2.json"
PY="$(cd ../backend && pwd)/.venv/Scripts/python.exe"
mkdir -p qa/v2
if [ ! -f data/index_v2.json ]; then (cd ../backend && $PY ingest.py) > qa/v2/ingest.log 2>&1; fi
tail -1 qa/v2/ingest.log
for sysname in plain_vector_k6 plain_hybrid_k6; do
  for r in 1 2 3 4; do
    ( $PY run_v2.py qa/v2/${sysname}_run$r.json $sysname > qa/v2/${sysname}_run$r.log 2>&1 ) &
  done
  wait
  for r in 1 2 3 4; do echo "$sysname run$r: $(tail -1 qa/v2/${sysname}_run$r.log)"; done
done
( $PY run_v2.py qa/v2/plain_vector_k4_run1.json plain_vector_k4 > qa/v2/plain_vector_k4_run1.log 2>&1 )
echo "plain_vector_k4 run1: $(tail -1 qa/v2/plain_vector_k4_run1.log)"
echo ALL DONE
