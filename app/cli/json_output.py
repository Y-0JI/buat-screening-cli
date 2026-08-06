"""CLI JSON output — kontrak data terstruktur (stabil, reusable).

Semua command dengan flag --json memakai helper di sini; struktur contract
ditest di tests/test_json_output.py. Bukan sekadar rendering — kontrak ini
juga dipakai TUI (Phase 3+) dan interface lain.
"""

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum


def sanitize(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(x) for x in obj]
    if hasattr(obj, "model_dump"):
        return sanitize(obj.model_dump())
    if is_dataclass(obj) and not isinstance(obj, type):
        return sanitize(asdict(obj))
    return str(obj)


def dump(obj) -> str:
    return json.dumps(sanitize(obj), ensure_ascii=False)


def research_report(report) -> dict:
    """Kontrak JSON `research --json` (ResearchReport -> dict stabil)."""
    sections = {}
    rd = report.research_data
    if rd is not None:
        for key, sec in rd.sections.items():
            sections[key] = {
                "status": sec.status.value,
                "source": sec.source,
                "data": sec.data,
                "reason": sec.reason,
            }
    return {
        "intent": sanitize(report.intent),
        "executive_summary": report.executive_summary,
        "recommendations": report.recommendations,
        "screening_results": report.screening_results,
        "sections": sections,
        "data_quality": report.data_quality,
        "failed": report.failed,
        "ai_failed": report.ai_failed,
    }


def providers_info(provider) -> list[dict]:
    stats = getattr(provider, "_stats", {}) or {}
    result = []
    for name, s in stats.items():
        ok, fail = s.get("ok", 0), s.get("fail", 0)
        rate = s.get("rate_limited", 0)
        error = s.get("error", 0)
        not_found = s.get("not_found", 0)
        if ok:
            status = "ok"
        elif rate:
            status = "rate_limited"
        elif error:
            status = "error"
        elif not_found:
            status = "not_found"
        elif fail:
            status = "degraded"
        else:
            status = "idle"
        result.append({
            "name": name,
            "status": status,
            "ok": ok,
            "fail": fail,
            "rate_limited": rate,
            "not_found": not_found,
            "error": error,
        })
    return result