from unittest.mock import patch

from app.tools.news import fetch_news, _parse_rss

_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<item><title>Headline Satu</title><link>https://example.com/1</link><pubDate>Tue, 04 Aug 2026 05:00:00 GMT</pubDate><source url="https://example.com">Contoh Media</source></item>
<item><title>Headline Dua</title><link>https://example.com/2</link><pubDate>Mon, 03 Aug 2026 10:30:00 GMT</pubDate></item>
</channel>
</rss>
"""


class _FakeResp:
    def __init__(self, text=""):
        self.text = text

    def raise_for_status(self):
        pass


class _FakeClient:
    def __init__(self, *a, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def get(self, url):
        if "gagal" in url:
            raise TimeoutError("timeout")
        return _FakeResp(_RSS)


def test_parse_rss_extracts_items():
    items = _parse_rss(_RSS)
    assert len(items) == 2
    assert items[0] == {
        "title": "Headline Satu",
        "link": "https://example.com/1",
        "published": "Tue, 04 Aug 2026 05:00:00 GMT",
        "source": "Contoh Media",
    }
    assert items[1]["source"] == "", "item tanpa source harus tetap diparse"


def test_parse_rss_invalid_and_doctype():
    assert _parse_rss("bukan xml") == []
    assert _parse_rss('<!DOCTYPE foo><rss><channel><item><title>X</title></item></channel></rss>') == [], "DOCTYPE harus ditolak"


def test_fetch_news_parses_and_limits():
    with patch("app.tools.news.httpx.Client", _FakeClient):
        out = fetch_news("PT Bank Contoh", limit=1)
    assert len(out) == 1
    assert out[0]["title"] == "Headline Satu"


def test_fetch_news_failure_returns_empty():
    with patch("app.tools.news.httpx.Client", _FakeClient):
        out = fetch_news("gagal semua")
    assert out == [], "kegagalan request harus return [], bukan raise"
