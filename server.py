#!/usr/bin/env python3
"""FastAPI MCP-style server for deterministic parking lookup."""

from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

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
        "properties": {
            "location": {"type": "string"},
        },
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

app = FastAPI()


class ToolCallRequest(BaseModel):
    name: str
    arguments: dict[str, Any] = {}


def find_parking(arguments: dict[str, Any]) -> dict[str, Any]:
    location = arguments.get("location")
    if not isinstance(location, str):
        return {"places": []}

    normalized = location.strip().lower()
    return {"places": PARKING_DATA.get(normalized, [])}


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/tools/list")
def tools_list() -> dict[str, list[dict[str, Any]]]:
    return {"tools": [TOOL_SCHEMA]}


@app.post("/tools/call")
def tools_call(payload: ToolCallRequest) -> dict[str, Any]:
    if payload.name != TOOL_NAME:
        return {"places": []}
    return find_parking(payload.arguments)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
