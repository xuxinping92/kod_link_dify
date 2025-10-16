"""
timer_runner.py — Lightweight, dependency‑free program scheduler.

Features
- Set a start time (absolute like "2025-10-16 18:00" or relative like "+15m").
- Set an interval ("30s", "5m", "2h30m").
- Limit number of launches via --times (0 means run forever).
- Cross‑platform; no external deps. Uses local system time.
- Graceful Stop (Ctrl+C) and exit code logging.

Usage (CLI)
-----------
# Run "python -m examples.demo6" first time at 18:00 today, then every 30 minutes, 5 times total
python timer_runner.py --cmd "python -m examples.demo6" --start "today 18:00" --every "30m" --times 5

# Start 10 minutes from now, repeat hourly, run forever
python timer_runner.py --cmd "C:\\Path\\to\\app.exe" --start "+10m" --every "1h" --times 0

# Start immediately, run only once
python timer_runner.py --cmd "echo hello"

Integrate in code
-----------------
from timer_runner import ProgramScheduler, parse_start_time, parse_interval

start_at = parse_start_time("today 18:00")
interval = parse_interval("30m")
sched = ProgramScheduler(["python", "-m", "examples.demo6"], start_at, interval, max_runs=5)
sched.run()  # blocking; use run_async() for non-blocking
"""

from __future__ import annotations

import re
import shlex
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Union

_RELATIVE_START_RE = re.compile(r"^\s*\+(\d+)([smhd])\s*$", re.I)
_TODAY_TIME_RE = re.compile(r"^\s*(today|tomorrow)\s+(\d{1,2}):(\d{2})\s*$", re.I)


def _now() -> datetime:
    # Local time (naive) for simplicity; matches typical CLI mental model
    return datetime.now()


def parse_interval(expr: Optional[str]) -> Optional[timedelta]:
    """
    Parse an interval string into timedelta.
    Accepts forms like: "30s", "5m", "2h", "2h30m", "1d2h15m", case-insensitive.
    Returns None if expr is None.
    Raises ValueError on bad format.
    """
    if expr is None:
        return None
    s = expr.strip().lower()
    if not s:
        return None

    # Tokenize like 1d2h30m10s
    total = timedelta(0)
    pattern = re.compile(r"(\d+)\s*([smhd])")
    pos = 0
    for m in pattern.finditer(s):
        val = int(m.group(1))
        unit = m.group(2)
        pos = m.end()
        if unit == "s":
            total += timedelta(seconds=val)
        elif unit == "m":
            total += timedelta(minutes=val)
        elif unit == "h":
            total += timedelta(hours=val)
        elif unit == "d":
            total += timedelta(days=val)
    if total.total_seconds() == 0 or pos != len(s):
        raise ValueError(f"Invalid interval expression: {expr!r}")
    return total


def parse_start_time(expr: Optional[str]) -> datetime:
    """
    Parse a start time expression into a datetime (local, naive).
    Supports:
    - None or empty: start immediately
    - "+15m", "+10s", "+2h", "+1d"
    - "today HH:MM" or "tomorrow HH:MM"
    - "YYYY-MM-DD HH:MM" (24h)
    - "YYYY-MM-DD HH:MM:SS"
    """
    if not expr:
        return _now()

    s = expr.strip()

    # Relative "+10m"
    m = _RELATIVE_START_RE.match(s)
    if m:
        amount = int(m.group(1))
        unit = m.group(2).lower()
        base = _now()
        if unit == "s":
            return base + timedelta(seconds=amount)
        if unit == "m":
            return base + timedelta(minutes=amount)
        if unit == "h":
            return base + timedelta(hours=amount)
        if unit == "d":
            return base + timedelta(days=amount)

    # today/tomorrow HH:MM
    m = _TODAY_TIME_RE.match(s)
    if m:
        day_word = m.group(1).lower()
        hh = int(m.group(2))
        mm = int(m.group(3))
        base = _now().replace(hour=0, minute=0, second=0, microsecond=0)
        if day_word == "tomorrow":
            base = base + timedelta(days=1)
        return base.replace(hour=hh, minute=mm)

    # Absolute "YYYY-MM-DD HH:MM[:SS]"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    raise ValueError(f"Invalid start time expression: {expr!r}")


@dataclass
class ProgramScheduler:
    command: Union[str, List[str]]
    start_at: datetime
    interval: Optional[timedelta] = None
    max_runs: int = 1
    shell: bool = False
    wait_for_exit: bool = True
    stop_on_error: bool = False

    def _as_argv(self) -> List[str]:
        if isinstance(self.command, list):
            return self.command
        # shlex.split works on POSIX; on Windows it's okay for many cases.
        # If paths have spaces, prefer passing list form to avoid quoting issues.
        return shlex.split(self.command, posix=(sys.platform != "win32"))

    def _sleep_until(self, dt: datetime) -> None:
        while True:
            now = _now()
            delta = (dt - now).total_seconds()
            if delta <= 0:
                return
            # sleep in small chunks to be interruptible
            time.sleep(min(1.0, delta))

    def _next_after(self, base: datetime, interval: timedelta) -> datetime:
        """Given base start time and interval, find the first run >= now."""
        now = _now()
        if now <= base:
            return base
        elapsed = (now - base).total_seconds()
        n = int(elapsed // interval.total_seconds()) + 1
        return base + n * interval

    def run(self) -> None:
        """
        Blocking runner. Honors max_runs and interval.
        If max_runs == 0, runs forever.
        """
        runs_done = 0

        if self.interval:
            next_run = self._next_after(self.start_at, self.interval)
        else:
            # one-off or repeated without interval (not common)
            next_run = self.start_at

        while True:
            self._sleep_until(next_run)

            runs_done += 1
            argv = self._as_argv()
            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Launching ({runs_done}):",
                argv,
                flush=True,
            )
            try:
                if self.wait_for_exit:
                    proc = subprocess.run(argv, shell=self.shell)
                    rc = proc.returncode
                else:
                    proc = subprocess.Popen(argv, shell=self.shell)
                    rc = 0  # optimistic; not waiting
                print(f"[INFO] Exit code: {rc}", flush=True)
                if rc != 0 and self.stop_on_error:
                    print("[ERROR] Non-zero exit. Stopping due to --stop-on-error.", flush=True)
                    break
            except KeyboardInterrupt:
                print("\n[INFO] Interrupted by user. Exiting.", flush=True)
                break
            except Exception as e:
                print(f"[ERROR] Failed to launch: {e}", flush=True)
                if self.stop_on_error:
                    break

            # Check completion
            if self.max_runs > 0 and runs_done >= self.max_runs:
                print("[INFO] Reached max runs. Done.", flush=True)
                break

            # Schedule next
            if self.interval:
                next_run = next_run + self.interval
                # if delayed (e.g., long job), catch up to next >= now
                if next_run < _now():
                    next_run = self._next_after(next_run, self.interval)
            else:
                # no interval => only one run
                if self.max_runs <= 1:
                    break
                # If user set times>1 but no interval, default to 1s
                next_run = _now() + timedelta(seconds=1)


def _build_arg_parser():
    import argparse

    p = argparse.ArgumentParser(description="Lightweight program scheduler")
    p.add_argument(
        "--cmd", required=True, help="Program/command to launch. Use quotes if it contains spaces."
    )
    p.add_argument(
        "--start",
        default="",
        help='Start time. Examples: "+10m", "today 18:00", "2025-10-16 18:30". Empty means now.',
    )
    p.add_argument("--every", default="", help='Interval. Examples: "30s", "5m", "2h30m".')
    p.add_argument("--times", type=int, default=1, help="Number of launches. 0 = run forever.")
    p.add_argument("--shell", action="store_true", help="Run the command via shell.")
    p.add_argument(
        "--no-wait",
        action="store_true",
        help="Do not wait for the process to finish before scheduling the next run.",
    )
    p.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop scheduling if a run exits with non-zero code.",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    start_at = parse_start_time(args.start or None)
    interval = parse_interval(args.every or None) if args.every else None
    max_runs = 0 if args.times == 0 else max(1, args.times)

    sched = ProgramScheduler(
        command=args.cmd,
        start_at=start_at,
        interval=interval,
        max_runs=max_runs,
        shell=args.shell,
        wait_for_exit=not args.no_wait,
        stop_on_error=args.stop_on_error,
    )
    try:
        sched.run()
        return 0
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted. Bye.", flush=True)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
