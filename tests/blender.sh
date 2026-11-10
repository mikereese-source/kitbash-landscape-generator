#!/usr/bin/env bash
# Run headless Blender 5.2, one process at a time across every session and worktree (Mike's rule):
# waits for a lock directory, runs, releases. A lock older than 30 minutes is treated as stale.
# Usage: tests/blender.sh [blender args...]   e.g. tests/blender.sh -b --factory-startup -P tests/run_tests.py
LOCK="${TEMP:-/tmp}/lg_blender.lock"
BLENDER="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
until mkdir "$LOCK" 2>/dev/null; do
  if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +30 2>/dev/null)" ]; then rmdir "$LOCK" 2>/dev/null; continue; fi
  sleep 5
done
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
"$BLENDER" "$@"
