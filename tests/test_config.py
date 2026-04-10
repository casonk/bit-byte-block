"""Tests for configuration helpers."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from bit_byte_block.config import load_env_file, load_proxy_config


class LoadEnvFileTests(unittest.TestCase):
    """Verify local env-file parsing behavior."""

    def test_load_env_file_sets_missing_values_and_preserves_existing(self) -> None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write(
                "# comment\nBIT_BYTE_BLOCK_BIND_HOST=127.0.0.1\nBIT_BYTE_BLOCK_LOG_LEVEL='DEBUG'\n"
            )
            path = handle.name

        try:
            with patch.dict(os.environ, {"BIT_BYTE_BLOCK_BIND_HOST": "0.0.0.0"}, clear=True):
                load_env_file(path)
                self.assertEqual(os.environ["BIT_BYTE_BLOCK_BIND_HOST"], "0.0.0.0")
                self.assertEqual(os.environ["BIT_BYTE_BLOCK_LOG_LEVEL"], "DEBUG")
        finally:
            os.unlink(path)

    def test_load_proxy_config_reads_environment_defaults(self) -> None:
        env = {
            "BIT_BYTE_BLOCK_BIND_HOST": "127.0.0.1",
            "BIT_BYTE_BLOCK_BIND_PORT": "23333",
            "BIT_BYTE_BLOCK_UPSTREAM_HOST": "solo4.ckpool.org",
            "BIT_BYTE_BLOCK_UPSTREAM_PORT": "3333",
            "BIT_BYTE_BLOCK_BACKUP_HOST": "",
            "BIT_BYTE_BLOCK_IDLE_TIMEOUT": "45",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_proxy_config()
        self.assertEqual(config.bind_host, "127.0.0.1")
        self.assertEqual(config.bind_port, 23333)
        self.assertEqual(config.upstream_host, "solo4.ckpool.org")
        self.assertIsNone(config.backup_host)
        self.assertEqual(config.idle_timeout, 45.0)
