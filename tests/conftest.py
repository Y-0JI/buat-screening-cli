import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def _no_network_news():
    with patch("app.agent.research.fetch_news", return_value=[]):
        yield
