"""Keep the RPM packaging files consistent with the Python package."""

from __future__ import annotations

import re
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGING = ROOT / "packaging"


def spec_field(name: str) -> str:
    text = (PACKAGING / "bit-byte-block.spec").read_text(encoding="utf-8")
    match = re.search(rf"^{name}:\s*(\S+)", text, re.MULTILINE)
    assert match, f"{name} missing from the spec"
    return match.group(1)


class PackagingTests(unittest.TestCase):
    def setUp(self) -> None:
        with (ROOT / "pyproject.toml").open("rb") as handle:
            self.project = tomllib.load(handle)["project"]

    def test_spec_version_matches_pyproject(self) -> None:
        self.assertEqual(spec_field("Version"), self.project["version"])

    def test_service_runs_the_console_script_with_the_packaged_settings(self) -> None:
        unit = (PACKAGING / "bit-byte-block.service").read_text(encoding="utf-8")
        self.assertIn("bit-byte-block", self.project["scripts"])
        self.assertIn("ExecStart=/usr/bin/bit-byte-block proxy", unit)
        self.assertIn("EnvironmentFile=-/etc/bit-byte-block/bit-byte-block.env", unit)

    def test_firewalld_port_matches_the_default_bind_port(self) -> None:
        service = (PACKAGING / "bit-byte-block.firewalld.xml").read_text(encoding="utf-8")
        example = (ROOT / "config" / "bit-byte-block.env.example").read_text(encoding="utf-8")
        port = re.search(r"^BIT_BYTE_BLOCK_BIND_PORT=(\d+)", example, re.MULTILINE).group(1)
        self.assertIn(f'port="{port}"', service)


if __name__ == "__main__":
    unittest.main()
