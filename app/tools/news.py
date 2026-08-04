import urllib.parse
import xml.etree.ElementTree as ET

import httpx


_NEWS_URL = "https://news.google.com/rss/search?q={q}&hl=id&gl=ID&ceid=ID:id"
_NEWS_LIMIT = 5
_TIMEOUT = 10
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; screening-cli/0.1)"}


def fetch_news(company_name: str, limit: int = _NEWS_LIMIT) -> list[dict]:
    url = _NEWS_URL.format(q=urllib.parse.quote(company_name))
    try:
        with httpx.Client(timeout=_TIMEOUT, headers=_HEADERS) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return _parse_rss(resp.text)[:limit]
    except Exception:
        return []


def _parse_rss(xml_text: str) -> list[dict]:
    if "<!DOCTYPE" in xml_text.upper():
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items = []
    for item in root.iter("item"):
        title = _child_text(item, "title")
        link = _child_text(item, "link")
        if not title or not link:
            continue
        items.append(
            {
                "title": title,
                "link": link,
                "published": _child_text(item, "pubDate"),
                "source": _child_text(item, "source"),
            }
        )
    return items


def _child_text(item: ET.Element, tag: str) -> str:
    for child in item:
        if child.tag.endswith(tag):
            return (child.text or "").strip()
    return ""
