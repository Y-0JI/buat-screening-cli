import asyncio
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


async def stream_process(proc: subprocess.Popen, write_line) -> int:
    """Baca stdout & stderr bersamaan (anti-deadlock), stream tiap baris via write_line.

    write_line dipanggil dari event loop (main thread) — aman untuk widget Textual
    tanpa call_from_thread: after to_thread selesai, coroutine kembali ke loop."""
    out = asyncio.create_task(_drain(proc.stdout, write_line))
    err = asyncio.create_task(_drain(proc.stderr, write_line))
    await asyncio.gather(out, err)
    return proc.wait()


async def _drain(stream, write_line) -> None:
    while True:
        line = await asyncio.to_thread(stream.readline)
        if not line:
            break
        write_line(line.rstrip("\n"))
