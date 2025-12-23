from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional


def _try_parse_dt(value: str | None) -> str | None:
    """Return ISO string if parseable, else the original string or None."""
    if not value:
        return None
    # EONET uses ISO-ish timestamps; keep it safe.
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.isoformat()
    except Exception:
        return value


@dataclass
class NormalizedGeometry:
    date: str | None
    type: str | None
    coordinates: Any  # can be [lon, lat] OR polygon etc.
    magnitude_value: float | None = None
    magnitude_unit: str | None = None


@dataclass
class NormalizedCategory:
    id: str
    title: str | None = None


@dataclass
class NormalizedSource:
    id: str
    url: str | None = None


@dataclass
class NormalizedEvent:
    id: str
    title: str | None
    description: str | None
    link: str | None
    status: str  # "open" or "closed"
    closed: str | None
    categories: List[NormalizedCategory]
    sources: List[NormalizedSource]
    geometry: List[NormalizedGeometry]


def normalize_events(eonet_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert EONET /events response to a stable internal format.

    EONET response shape:
      { "title": "...", "events": [ { id, title, description, link, closed, categories, sources, geometry } ] }
    Docs: https://eonet.gsfc.nasa.gov/docs/v3
    """
    raw_events = eonet_payload.get("events", []) or []
    normalized: List[NormalizedEvent] = []

    for ev in raw_events:
        ev_id = str(ev.get("id", ""))
        title = ev.get("title")
        desc = ev.get("description")
        link = ev.get("link")

        closed = _try_parse_dt(ev.get("closed"))
        status = "closed" if closed else "open"

        categories = []
        for c in (ev.get("categories") or []):
            categories.append(
                NormalizedCategory(
                    id=str(c.get("id", "")),
                    title=c.get("title"),
                )
            )

        sources = []
        for s in (ev.get("sources") or []):
            sources.append(
                NormalizedSource(
                    id=str(s.get("id", "")),
                    url=s.get("url"),
                )
            )

        geom_list = []
        for g in (ev.get("geometry") or []):
            geom_list.append(
                NormalizedGeometry(
                    date=_try_parse_dt(g.get("date")),
                    type=g.get("type"),
                    coordinates=g.get("coordinates"),
                    magnitude_value=g.get("magnitudeValue"),
                    magnitude_unit=g.get("magnitudeUnit"),
                )
            )

        normalized.append(
            NormalizedEvent(
                id=ev_id,
                title=title,
                description=desc,
                link=link,
                status=status,
                closed=closed,
                categories=categories,
                sources=sources,
                geometry=geom_list,
            )
        )

    # Return a wrapper that your frontend/next layers can rely on.
    return {
        "source": "NASA_EONET_V3",
        "title": eonet_payload.get("title"),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "count": len(normalized),
        "events": [asdict(e) for e in normalized],
    }