"""Integration-style tests for the TCP proxy."""

from __future__ import annotations

import asyncio
import unittest

from bit_byte_block.config import ProxyConfig
from bit_byte_block.proxy import StratumProxyServer


async def _start_line_server(
    received: list[bytes],
    reply: bytes,
) -> tuple[asyncio.base_events.Server, int]:
    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.readline()
        received.append(data)
        writer.write(reply)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, port


class ProxyTests(unittest.IsolatedAsyncioTestCase):
    """Validate relay and backup-upstream behavior."""

    async def asyncTearDown(self) -> None:
        await asyncio.sleep(0)

    async def test_proxy_relays_data_between_client_and_upstream(self) -> None:
        upstream_received: list[bytes] = []
        upstream_server, upstream_port = await _start_line_server(
            upstream_received,
            b'{"id": 1, "result": true}\n',
        )

        config = ProxyConfig(
            bind_host="127.0.0.1",
            bind_port=0,
            upstream_host="127.0.0.1",
            upstream_port=upstream_port,
            backup_host=None,
            idle_timeout=5.0,
        )
        proxy = StratumProxyServer(config)
        await proxy.start()
        assert proxy._server is not None
        proxy_port = proxy._server.sockets[0].getsockname()[1]
        serve_task = asyncio.create_task(proxy.serve_forever())

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
            writer.write(b'{"id": 1, "method": "mining.subscribe"}\n')
            await writer.drain()
            response = await reader.readline()
            self.assertEqual(response, b'{"id": 1, "result": true}\n')
            self.assertEqual(upstream_received, [b'{"id": 1, "method": "mining.subscribe"}\n'])
            writer.close()
            await writer.wait_closed()
        finally:
            await proxy.close()
            serve_task.cancel()
            await asyncio.gather(serve_task, return_exceptions=True)
            upstream_server.close()
            await upstream_server.wait_closed()

    async def test_proxy_fails_over_to_backup_upstream(self) -> None:
        backup_received: list[bytes] = []
        backup_server, backup_port = await _start_line_server(
            backup_received,
            b'{"id": 2, "result": "backup"}\n',
        )

        config = ProxyConfig(
            bind_host="127.0.0.1",
            bind_port=0,
            upstream_host="127.0.0.1",
            upstream_port=9,
            backup_host="127.0.0.1",
            backup_port=backup_port,
            connect_timeout=0.5,
            idle_timeout=5.0,
        )
        proxy = StratumProxyServer(config)
        await proxy.start()
        assert proxy._server is not None
        proxy_port = proxy._server.sockets[0].getsockname()[1]
        serve_task = asyncio.create_task(proxy.serve_forever())

        try:
            reader, writer = await asyncio.open_connection("127.0.0.1", proxy_port)
            writer.write(b'{"id": 2, "method": "mining.authorize"}\n')
            await writer.drain()
            response = await reader.readline()
            self.assertEqual(response, b'{"id": 2, "result": "backup"}\n')
            self.assertEqual(backup_received, [b'{"id": 2, "method": "mining.authorize"}\n'])
            writer.close()
            await writer.wait_closed()
        finally:
            await proxy.close()
            serve_task.cancel()
            await asyncio.gather(serve_task, return_exceptions=True)
            backup_server.close()
            await backup_server.wait_closed()
