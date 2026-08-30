#!/usr/bin/env python3
"""Backstop for GitHub's unreliable Actions cron (see fetch_conditions.yml).

Runs every 20 min via launchd (com.joshuaedrake.ahf-dispatch). If the newest
fetch_conditions run started more than STALE_SECONDS ago, fires a
workflow_dispatch through the locally-authed gh CLI. No stored secrets.

Runtime copy lives at ~/.config/ahf/dispatch_watchdog.py (launchd-spawned
python3 is TCC-blocked from ~/Documents) — re-copy there after editing this.
ponytail: Mac-asleep = no backstop; native cron still fires sometimes, good enough.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone

REPO = "us41242/alwayshave-fun"
WORKFLOW = "fetch_conditions.yml"
GH = "/opt/homebrew/bin/gh"
STALE_SECONDS = 40 * 60


def main():
    out = subprocess.run(
        [GH, "run", "list", "-R", REPO, "-w", WORKFLOW, "-L", "1",
         "--json", "createdAt"],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        print(f"gh run list failed: {out.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    runs = json.loads(out.stdout)
    last = datetime.fromisoformat(runs[0]["createdAt"].replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - last).total_seconds()
    if age < STALE_SECONDS:
        print(f"fresh: last run {age/60:.0f} min ago, nothing to do")
        return
    disp = subprocess.run(
        [GH, "workflow", "run", WORKFLOW, "-R", REPO],
        capture_output=True, text=True, timeout=60)
    if disp.returncode != 0:
        print(f"dispatch failed: {disp.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    print(f"stale: last run {age/60:.0f} min ago — dispatched {WORKFLOW}")


if __name__ == "__main__":
    main()
