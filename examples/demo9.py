"""
demo_schedule.py — tiny examples for timer_runner.ProgramScheduler
"""

from kod_link_dify.utils.timer_runner import ProgramScheduler, parse_interval, parse_start_time


def main():
    # Example 1: run "echo hello" 3 times, start 10s from now, every 5s
    start = parse_start_time("+10s")
    interval = parse_interval("5s")
    sched = ProgramScheduler(
        "python -c \"print('hello from scheduled run')\"", start, interval, max_runs=3, shell=True
    )
    sched.run()


if __name__ == "__main__":
    main()
