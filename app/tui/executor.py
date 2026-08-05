import shutil
import subprocess
import sys
from abc import ABC, abstractmethod

from app.tui.registry import Feature


class Executor(ABC):
    @abstractmethod
    def run(self, feature: Feature) -> subprocess.Popen:
        """Jalankan fitur, kembalikan proses dengan stdout/stderr PIPE."""


class SubprocessExecutor(Executor):
    def run(self, feature: Feature) -> subprocess.Popen:
        bin_path = shutil.which("screening")
        argv = [bin_path] + feature.command if bin_path else [sys.executable, "-m", "app.cli.main"] + feature.command
        return subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
