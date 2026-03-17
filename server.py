#!/usr/bin/env python3
"""Deterministic OpenAI task app server for finding parking."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8000"))
TOOL_NAME = "find_parking"

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
    "input": {
        "type": "object",
        "properties": {"location": {"type": "string"}},
        "required": ["location"],
    },
    "output": {
        "places": [
            {
                "name": "string",
                "address": "string",
                "lat": 0,
                "lng": 0,
            }
        ]
    },
}

TOOL_DEFINITIONS = [TOOL_SCHEMA]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json(self) -> dict[str, Any] | None:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_text(self, status: int, text: str) -> None:
        encoded = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    @staticmethod
    def _find_parking(arguments: dict[str, Any]) -> dict[str, Any]:
        location = arguments.get("location")
        if not isinstance(location, str):
            return {"places": []}
        normalized = location.strip().lower()
        return {"places": PARKING_DATA.get(normalized, [])}

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/.well-known/openai-apps-challenge":
            self._send_json(200, {"challenge": os.environ.get("OPENAI_APPS_CHALLENGE", "PLACEHOLDER_TOKEN")})
            return
        if self.path == "/privacy":
            self._send_text(200, "Privacy policy: no user data is stored.")
            return
        if self.path == "/terms":
            self._send_text(200, "Terms: use as-is.")
            return
        if self.path == "/support":
            self._send_text(200, "Support: support@example.com")
            return
        if self.path == "/mcp":
            self._send_json(200, {"tools": TOOL_DEFINITIONS})
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self._send_json(404, {"error": "not_found"})
            return

        request = self._read_json()
        if request is None:
            self._send_json(400, {"error": "invalid_json"})
            return

        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params") or {}

        if method == "tools/list":
            self._send_json(200, {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOL_DEFINITIONS}})
            return

        if method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") if isinstance(params, dict) else {}
            if not isinstance(arguments, dict):
                arguments = {}
            if name != TOOL_NAME:
                result = {"places": []}
            else:
                result = self._find_parking(arguments)
            self._send_json(200, {"jsonrpc": "2.0", "id": request_id, "result": result})
            return

        self._send_json(200, {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()
