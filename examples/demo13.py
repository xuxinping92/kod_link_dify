# 测试计时器同步可道云文件夹内所有文件到dify知识库

import sys

from kod_link_dify.utils.timer_runner import ProgramScheduler, parse_interval, parse_start_time


def main():
    # 自动获取当前虚拟环境的解释器
    python_path = sys.executable
    print("Using interpreter:", python_path)

    start_at = parse_start_time("+10s")
    interval = parse_interval("1m")

    sched = ProgramScheduler(
        [python_path, "-m", "examples.demo12"],
        start_at,
        interval,
        max_runs=4,
    )
    sched.run()


if __name__ == "__main__":
    main()
