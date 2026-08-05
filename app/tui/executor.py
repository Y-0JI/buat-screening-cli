import shutil
import subprocess
import sys
from abc import ABC, abstractmethod


class Executor(ABC):
    @abstractmethod
    def run(self, argv: list[str]) -> subprocess.Popen:
        """Jalankan argv CLI, kembalikan proses dengan stdout/stderr PIPE."""


class SubprocessExecutor(Executor):
    def run(self, argv: list[str]) -> subprocess.Popen:
        bin_path = shutil.which("screening")
        full = [bin_path] + argv if bin_path else [sys.executable, "-m", "app.cli.main"] + argv
        return subprocess.Popen(
            full,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
