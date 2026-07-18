"""Launch one local development service in an independent process session."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--pid-file", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a command is required after --")
    return args


def main() -> None:
    args = parse_args()
    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.pid_file.parent.mkdir(parents=True, exist_ok=True)

    with args.log.open("ab", buffering=0) as log_file:
        process = subprocess.Popen(  # noqa: S603 - command is repository-owned developer tooling
            args.command,
            cwd=args.cwd,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )

    temporary_pid_file = args.pid_file.with_suffix(f"{args.pid_file.suffix}.tmp")
    temporary_pid_file.write_text(f"{process.pid}\n", encoding="ascii")
    temporary_pid_file.replace(args.pid_file)


if __name__ == "__main__":
    main()
