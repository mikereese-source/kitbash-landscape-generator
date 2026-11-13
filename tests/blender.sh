#!/usr/bin/env bash
# Run headless Blender 5.2, one process at a time across every session and worktree (Mike's rule):
# waits for a lock directory, runs, releases. A lock whose holder has exited is treated as stale.
# Usage: tests/blender.sh [blender args...]   e.g. tests/blender.sh -b --factory-startup -P tests/run_tests.py
LOCK="${TEMP:-/tmp}/lg_blender.lock"
BLENDER="${LG_BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"  # LG_BLENDER tries another version
until mkdir "$LOCK" 2>/dev/null; do
  # Stale only when its holder is gone: a full suite runs past 30 minutes, and a time limit let a second Blender in (2026-11-13).
  pid=$(cat "$LOCK/pid" 2>/dev/null)
  if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then rm -rf "$LOCK"; continue; fi
  if [ -z "$pid" ] && [ -n "$(find "$LOCK" -maxdepth 0 -mmin +30 2>/dev/null)" ]; then rm -rf "$LOCK"; continue; fi  # an old lock without a pid
  sleep 5
done
echo $$ > "$LOCK/pid"
trap 'rm -rf "$LOCK"' EXIT
"$BLENDER" "$@"
