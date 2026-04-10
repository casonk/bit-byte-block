"""Upstream monitoring helpers for Solo CKPool."""

from __future__ import annotations

import json
from typing import Any
from urllib.request import urlopen


def parse_json_stream(payload: str) -> list[dict[str, Any]]:
    """Parse adjacent JSON objects separated by whitespace."""
    decoder = json.JSONDecoder()
    values: list[dict[str, Any]] = []
    index = 0
    while index < len(payload):
        while index < len(payload) and payload[index].isspace():
            index += 1
        if index >= len(payload):
            break
        value, next_index = decoder.raw_decode(payload, index)
        if not isinstance(value, dict):
            raise ValueError("expected JSON object in pool status payload")
        values.append(value)
        index = next_index
    return values


def fetch_pool_status_snapshot(url: str, timeout: float = 10.0) -> dict[str, Any]:
    """Fetch and normalize the pool-status response into named sections."""
    with urlopen(url, timeout=timeout) as response:  # noqa: S310 - user-supplied public status URL
        payload = response.read().decode("utf-8")
    sections = parse_json_stream(payload)
    if len(sections) != 3:
        raise ValueError(f"expected 3 JSON objects in pool status payload, found {len(sections)}")
    return {
        "summary": sections[0],
        "hashrate": sections[1],
        "shares": sections[2],
    }
