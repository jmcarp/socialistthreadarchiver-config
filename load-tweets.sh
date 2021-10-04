#!/usr/bin/env bash

set -euo pipefail

user=socialistdogmom

data_dir="twint/$user"
mkdir -p "$data_dir"
last_file=$(find "$data_dir" -type f | sort | tail -n1)
if [ -n "$last_file" ]; then
  since=$(head -n1 "$last_file" | jq -r '(.date + " " + .time)')
else
  since=""
fi

data_path="$data_dir/$(TZ=UTC date +%s).json"
twint -u "$user" -o "$data_path" --since "$since" --json
