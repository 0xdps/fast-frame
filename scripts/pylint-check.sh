#!/usr/bin/env bash
# Same pylint gate as CI: warnings (exit 4 or 6) are allowed.
# Exit 2, or any E/F message, fails the check.
set -uo pipefail

output="$(mktemp)"
trap 'rm -f "$output"' EXIT

pylint src/fastframe --fail-on=E,F --output-format=text >"$output"
code=$?
cat "$output"

if [ "$code" -eq 2 ] || grep -E ': [EF][0-9]{4}:' "$output"; then
  exit 2
fi
exit 0
