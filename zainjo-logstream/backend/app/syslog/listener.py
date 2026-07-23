"""
Async UDP and TCP syslog listeners.

Both listeners put ParsedSyslog objects onto a shared asyncio.Queue
consumed by the log processor workers.
"""
import asyncio
import logging
from typing import Optional

from app.config import settings
from app.syslog.parser import parse_syslog, ParsedSyslog

logger = logging.getLogger(__name__)

# Shared ingestion queue. Populated by listeners, consumed by processor workers.
log_queue: asyncio.Queue[ParsedSyslog] = asyncio.Queue(maxsize=settings.syslog_queue_size)


# ─── UDP ─────────────────────────────────────────────────────────────────────

class _SyslogUDPProtocol(asyncio.DatagramProtocol):
    """asyncio UDP protocol that feeds parsed messages into log_queue."""

    def __init__(self, queue: asyncio.Queue) -> None:
        self._queue = queue
        self._dropped = 0

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        try:
            raw = data.decode("utf-8", errors="replace").strip()
            source_ip = addr[0]
            parsed = parse_syslog(raw, source_ip)
            try:
                self._queue.put_nowait(parsed)
            except asyncio.QueueFull:
                self._dropped += 1
                if self._dropped % 1000 == 0:
                    logger.warning(
                        "Ingestion queue full — dropped %d UDP messages so far", self._dropped
                    )
        except Exception:
            logger.exception("Error in UDP datagram_received")

    def error_received(self, exc: Exception) -> None:
        logger.error("UDP socket error: %s", exc)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if exc:
            logger.error("UDP connection lost: %s", exc)


async def start_udp_listener(host: str, port: int, queue: asyncio.Queue) -> asyncio.BaseTransport:
    """Start the async UDP syslog listener."""
    loop = asyncio.get_running_loop()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _SyslogUDPProtocol(queue),
        local_addr=(host, port),
        reuse_port=True,
    )
    logger.info("UDP syslog listener started on %s:%d", host, port)
    return transport


# ─── TCP ─────────────────────────────────────────────────────────────────────

async def _handle_tcp_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    queue: asyncio.Queue,
) -> None:
    """Handle a single TCP syslog client connection."""
    addr = writer.get_extra_info("peername")
    source_ip = addr[0] if addr else "unknown"
    try:
        while True:
            # Syslog over TCP: each message ends with \n (octet-framing not implemented yet)
            line = await asyncio.wait_for(reader.readline(), timeout=300)
            if not line:
                break
            raw = line.decode("utf-8", errors="replace").strip()
            if not raw:
                continue
            parsed = parse_syslog(raw, source_ip)
            try:
                await asyncio.wait_for(queue.put(parsed), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Queue full — TCP message from %s dropped", source_ip)
    except asyncio.TimeoutError:
        pass  # idle connection closed
    except asyncio.IncompleteReadError:
        pass  # client disconnected
    except Exception:
        logger.exception("Error handling TCP client %s", source_ip)
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def start_tcp_listener(host: str, port: int, queue: asyncio.Queue) -> asyncio.Server:
    """Start the async TCP syslog listener."""
    server = await asyncio.start_server(
        lambda r, w: _handle_tcp_client(r, w, queue),
        host=host,
        port=port,
        reuse_port=True,
        limit=settings.syslog_buffer_size,
    )
    logger.info("TCP syslog listener started on %s:%d", host, port)
    return server


# ─── Start both ──────────────────────────────────────────────────────────────

async def start_listeners() -> list:
    """Start enabled syslog listeners and return handles for graceful shutdown."""
    handles = []
    host = settings.syslog_host
    port = settings.syslog_port

    if settings.syslog_udp_enabled:
        udp = await start_udp_listener(host, port, log_queue)
        handles.append(udp)

    if settings.syslog_tcp_enabled:
        tcp = await start_tcp_listener(host, port, log_queue)
        handles.append(tcp)

    return handles
