#!/usr/bin/env python3
"""Minimal deterministic MCP server for find parking."""

from __future__ import annotations

import json
import sys
from typing import Any

TOOL_NAME = "find_parking"

# Deterministic, static dataset keyed by normalized location.
PARKING_DATA: dict[str, list[dict[str, Any]]] = {
    "downtown": [
        {
            "name": "Downtown Central Garage",
            "address": "100 Main St",
            "lat": 37.7749,
            "lng": -122.4194,
        },
        {
            "name": "Market Street Parking",
            "address": "250 Market St",
            "lat": 37.7936,
            "lng": -122.3958,
        },
    ],
    "airport": [
        {
            "name": "Airport Long Term Lot A",
            "address": "1 Aviation Way",
            "lat": 37.6213,
            "lng": -122.379,
        }
    ],
    "city center": [
        {
            "name": "City Center Parking Deck",
            "address": "50 Center Plaza",
            "lat": 40.7128,
            "lng": -74.006,
        }
    ],
}

TOOL_SCHEMA = {
    "name": TOOL_NAME,
    "description": "Return deterministic parking places for a location.",
    "inputSchema": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
}


def make_result(payload: Any, request_id: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": payload}


def make_error(code: int, message: str, request_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def find_parking(arguments: dict[str, Any]) -> dict[str, Any]:
    location = arguments.get("location")
    if not isinstance(location, str):
        return {"places": []}

    normalized = location.strip().lower()
    places = PARKING_DATA.get(normalized, [])
    return {"places": places}


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    if method == "tools/list":
        return make_result({"tools": [TOOL_SCHEMA]}, request_id)

    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        if name != TOOL_NAME:
            return make_result({"places": []}, request_id)
        return make_result(find_parking(arguments), request_id)

    if method in {"health", "health/check"}:
        return make_result({"status": "ok"}, request_id)

    if request_id is None:
        return None
    return make_error(-32601, "Method not found", request_id)


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(make_error(-32700, "Parse error", None)) + "\n")
            sys.stdout.flush()
            continue

        if not isinstance(request, dict):
            sys.stdout.write(json.dumps(make_error(-32600, "Invalid Request", None)) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
