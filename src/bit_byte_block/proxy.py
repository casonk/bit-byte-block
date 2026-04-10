"""Asyncio TCP proxy for Stratum-compatible miners."""

from __future__ import annotations

import asyncio
import logging
import socket
from collections.abc import Awaitable, Callable

from .config import ProxyConfig

LOGGER = logging.getLogger(__name__)
BufferReader = asyncio.StreamReader
BufferWriter = asyncio.StreamWriter


def _set_tcp_nodelay(writer: BufferWriter) -> None:
    sock = writer.get_extra_info("socket")
    if sock is None:
        return
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError:
        LOGGER.debug("unable to enable TCP_NODELAY", exc_info=True)


async def _pipe(
    source: BufferReader,
    destination: BufferWriter,
    idle_timeout: float,
    direction: str,
) -> None:
    while True:
        try:
            chunk = await asyncio.wait_for(source.read(65536), timeout=idle_timeout)
        except TimeoutError:
            LOGGER.info("%s idle timeout after %.1fs", direction, idle_timeout)
            break
        if not chunk:
            break
        destination.write(chunk)
        await destination.drain()


class StratumProxyServer:
    """Transparent TCP proxy suitable for local Stratum traffic."""

    def __init__(
        self,
        config: ProxyConfig,
        server_factory: Callable[..., Awaitable[asyncio.base_events.Server]] | None = None,
    ) -> None:
        self.config = config
        self._server_factory = server_factory or asyncio.start_server
        self._server: asyncio.base_events.Server | None = None

    async def start(self) -> None:
        """Start listening for incoming miner connections."""
        self._server = await self._server_factory(
            self._handle_client,
            self.config.bind_host,
            self.config.bind_port,
        )

    async def serve_forever(self) -> None:
        """Block until the server is stopped."""
        if self._server is None:
            raise RuntimeError("proxy server has not been started")
        async with self._server:
            await self._server.serve_forever()

    async def close(self) -> None:
        """Close the listening socket."""
        if self._server is None:
            return
        self._server.close()
        await self._server.wait_closed()
        self._server = None

    async def _open_upstream(self) -> tuple[BufferReader, BufferWriter, str]:
        endpoints: list[tuple[str, int]] = [(self.config.upstream_host, self.config.upstream_port)]
        if self.config.backup_host:
            endpoints.append((self.config.backup_host, self.config.backup_port))

        last_error: OSError | TimeoutError | None = None
        for host, port in endpoints:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, port),
                    timeout=self.config.connect_timeout,
                )
                _set_tcp_nodelay(writer)
                return reader, writer, f"{host}:{port}"
            except (OSError, TimeoutError) as exc:
                LOGGER.warning("upstream connection failed for %s:%s", host, port, exc_info=True)
                last_error = exc
        assert last_error is not None
        raise last_error

    async def _handle_client(self, reader: BufferReader, writer: BufferWriter) -> None:
        client_peer = writer.get_extra_info("peername")
        _set_tcp_nodelay(writer)
        LOGGER.info("accepted miner connection from %s", client_peer)

        try:
            upstream_reader, upstream_writer, upstream_name = await self._open_upstream()
        except (OSError, TimeoutError):
            LOGGER.error("unable to connect upstream for client %s", client_peer, exc_info=True)
            writer.close()
            await writer.wait_closed()
            return

        LOGGER.info("client %s connected upstream to %s", client_peer, upstream_name)

        tasks = {
            asyncio.create_task(
                _pipe(reader, upstream_writer, self.config.idle_timeout, "miner->upstream")
            ),
            asyncio.create_task(
                _pipe(upstream_reader, writer, self.config.idle_timeout, "upstream->miner")
            ),
        }

        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                await task
        finally:
            upstream_writer.close()
            writer.close()
            await asyncio.gather(
                upstream_writer.wait_closed(),
                writer.wait_closed(),
                return_exceptions=True,
            )
            LOGGER.info("closed miner connection from %s", client_peer)
