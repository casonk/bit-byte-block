"""Tests for pool-status parsing."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from bit_byte_block.monitor import fetch_pool_status_snapshot, parse_json_stream


class FakeResponse:
    """Simple context-manager wrapper for mocked urlopen responses."""

    def __init__(self, payload: str) -> None:
        self._payload = payload.encode("utf-8")

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


class MonitorTests(unittest.TestCase):
    """Pool status parsing coverage."""

    def test_parse_json_stream_reads_three_adjacent_objects(self) -> None:
        payload = '{"a": 1} {"b": 2}\n{"c": 3}'
        self.assertEqual(parse_json_stream(payload), [{"a": 1}, {"b": 2}, {"c": 3}])

    def test_fetch_pool_status_snapshot_labels_sections(self) -> None:
        payload = (
            '{"runtime": 10, "Users": 1} '
            '{"hashrate1m": "1P", "hashrate5m": "2P"} '
            '{"accepted": 3, "bestshare": 4}'
        )
        with patch("bit_byte_block.monitor.urlopen", return_value=FakeResponse(payload)):
            snapshot = fetch_pool_status_snapshot("https://solo.ckpool.org/pool/pool.status")
        self.assertEqual(snapshot["summary"]["runtime"], 10)
        self.assertEqual(snapshot["hashrate"]["hashrate1m"], "1P")
        self.assertEqual(snapshot["shares"]["bestshare"], 4)


class ExtraSectionTests(unittest.TestCase):
    """The pool appends sections over time; only the first three are required."""

    def fetch(self, payload: str) -> dict:
        with patch("bit_byte_block.monitor.urlopen", return_value=FakeResponse(payload)):
            return fetch_pool_status_snapshot("https://solo.ckpool.org/pool/pool.status")

    def test_extra_sections_are_kept(self) -> None:
        snapshot = self.fetch(
            '{"runtime": 10} {"hashrate1m": "1P"} {"bestshare": 4} {"clients": 32} {"sv2jd": true}'
        )
        self.assertEqual(snapshot["shares"]["bestshare"], 4)
        self.assertEqual(snapshot["extra"], [{"clients": 32}, {"sv2jd": True}])

    def test_fewer_than_three_sections_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            self.fetch('{"runtime": 10} {"hashrate1m": "1P"}')
