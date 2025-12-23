from __future__ import annotations

from flask import Blueprint, jsonify, request

from nasa.client import EONETClient, EONETClientError
from nasa.normalizer import normalize_events

nasa_bp = Blueprint("nasa", __name__, url_prefix="/api/nasa")

client = EONETClient()


def _get_query_params():
    """
    Shared query parameters:
      category: e.g. "wildfires" (see /categories)
      source:   e.g. "InciWeb" (see /sources)
      status:   "open" or "closed"
      days:     integer
      limit:    integer
    """
    category = request.args.get("category") or None
    source = request.args.get("source") or None
    status = request.args.get("status") or None

    days = request.args.get("days")
    days_int = int(days) if days and days.isdigit() else None

    limit = request.args.get("limit")
    limit_int = int(limit) if limit and limit.isdigit() else None

    return category, source, status, days_int, limit_int


@nasa_bp.get("/raw/events")
def raw_events():
    category, source, status, days, limit = _get_query_params()
    try:
        payload = client.get_events(
            category=category,
            source=source,
            status=status,
            days=days,
            limit=limit,
        )
        return jsonify(payload), 200
    except EONETClientError as e:
        return jsonify({"error": "EONET_UPSTREAM_ERROR", "message": str(e)}), 502


@nasa_bp.get("/normalized/events")
def normalized_events():
    category, source, status, days, limit = _get_query_params()
    try:
        payload = client.get_events(
            category=category,
            source=source,
            status=status,
            days=days,
            limit=limit,
        )
        normalized = normalize_events(payload)
        return jsonify(normalized), 200
    except EONETClientError as e:
        return jsonify({"error": "EONET_UPSTREAM_ERROR", "message": str(e)}), 502


@nasa_bp.get("/categories")
def categories():
    try:
        payload = client.get_categories()
        return jsonify(payload), 200
    except EONETClientError as e:
        return jsonify({"error": "EONET_UPSTREAM_ERROR", "message": str(e)}), 502


@nasa_bp.get("/sources")
def sources():
    try:
        payload = client.get_sources()
        return jsonify(payload), 200
    except EONETClientError as e:
        return jsonify({"error": "EONET_UPSTREAM_ERROR", "message": str(e)}), 502
