#!/usr/bin/env bash
set -euo pipefail

PARALLEL=0
if [[ "${1:-}" == "--parallel" ]]; then
  PARALLEL=1
fi

CONSOLE_LOG_DIR="data/results/runs/_console"
mkdir -p "$CONSOLE_LOG_DIR"
CONFIG_DIR="experiments/configs"
CONFIG_JSON_DIR="$CONFIG_DIR/json"
shopt -s nullglob

# Prefer YAML when both exist (same basename): .yaml > .yml > .json (json/ subfolder)
mapfile -t basenames < <(
  {
    for f in "$CONFIG_DIR"/*.yaml "$CONFIG_DIR"/*.yml "$CONFIG_JSON_DIR"/*.json; do
      [[ -e "$f" ]] || continue
      basename "$f" | sed -E 's/\.(json|yaml|yml)$//'
    done
  } | sort -u
)

for base in "${basenames[@]}"; do
  cfg=""
  if [[ -f "$CONFIG_DIR/${base}.yaml" ]]; then
    cfg="$CONFIG_DIR/${base}.yaml"
  elif [[ -f "$CONFIG_DIR/${base}.yml" ]]; then
    cfg="$CONFIG_DIR/${base}.yml"
  elif [[ -f "$CONFIG_JSON_DIR/${base}.json" ]]; then
    cfg="$CONFIG_JSON_DIR/${base}.json"
  elif [[ -f "$CONFIG_DIR/${base}.json" ]]; then
    cfg="$CONFIG_DIR/${base}.json"
  fi
  [[ -n "$cfg" ]] || continue

  name="$base"
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

echo "All experiments finished."
