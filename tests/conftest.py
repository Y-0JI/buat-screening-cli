import os
from pathlib import Path

import pytest
from unittest.mock import patch

_VENV_BIN = Path(__file__).resolve().parents[1] / ".venv" / "bin"
os.environ["PATH"] = f"{_VENV_BIN}:{os.environ.get('PATH', '')}"


@pytest.fixture(autouse=True)
def _no_network_news():
    with patch("app.agent.research.fetch_news", return_value=[]):
        yield
