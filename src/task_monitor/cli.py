import argparse
import sys
from pathlib import Path

from .orchestrator import run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="task_monitor")
    parser.add_argument("--config", required=True, help="TOML config file path")
    parser.add_argument("--job", required=True, help="job name to monitor")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run(Path(args.config), args.job)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

