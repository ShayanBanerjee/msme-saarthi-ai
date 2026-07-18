from __future__ import annotations

import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT_DIR / "scripts" / "run-detached.py"


class DetachedLauncherTest(unittest.TestCase):
    def test_launches_command_in_an_independent_session(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            marker = directory / "ready"
            pid_file = directory / "service.pid"
            log_file = directory / "service.log"
            command = [
                sys.executable,
                "-c",
                f"from pathlib import Path; import time; Path({str(marker)!r}).write_text('ready'); time.sleep(10)",
            ]

            subprocess.run(
                [
                    sys.executable,
                    str(LAUNCHER),
                    "--cwd",
                    str(directory),
                    "--log",
                    str(log_file),
                    "--pid-file",
                    str(pid_file),
                    "--",
                    *command,
                ],
                check=True,
            )
            pid = int(pid_file.read_text(encoding="ascii"))
            try:
                for _ in range(50):
                    if marker.exists():
                        break
                    time.sleep(0.02)
                self.assertTrue(marker.exists())
                self.assertEqual(os.getsid(pid), pid)
            finally:
                os.kill(pid, signal.SIGTERM)


if __name__ == "__main__":
    unittest.main()
