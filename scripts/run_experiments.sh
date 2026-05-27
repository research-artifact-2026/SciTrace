#!/usr/bin/env bash
set -euo pipefail

PARALLEL=0
if [[ "${1:-}" == "--parallel" ]]; then
  PARALLEL=1
fi

CONSOLE_LOG_DIR="results/runs/_console"
CONFIG_DIR="configs/main"
mkdir -p "$CONSOLE_LOG_DIR"
shopt -s nullglob
configs=("$CONFIG_DIR"/*.yaml)

if [[ "${#configs[@]}" -eq 0 ]]; then
  echo "No primary YAML configs found in $CONFIG_DIR" >&2
  exit 1
fi

for cfg in "${configs[@]}"; do
  name="$(basename "$cfg" .yaml)"
  if [[ "$PARALLEL" -eq 1 ]]; then
    python scripts/run_single_config.py --config "$cfg" >"${CONSOLE_LOG_DIR}/${name}.log" 2>&1 &
  else
    echo "Running $cfg"
    python scripts/run_single_config.py --config "$cfg" | tee "${CONSOLE_LOG_DIR}/${name}.log"
  fi
done

if [[ "$PARALLEL" -eq 1 ]]; then
  wait
fi

echo "All primary experiments finished."
