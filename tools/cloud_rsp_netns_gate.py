#!/usr/bin/env python3
"""Fail-closed, TEST-FIXTURE-ONLY network namespace preflight.

Must be paired with a host-verified --network none container. No private ROM.
"""
from __future__ import annotations
import ipaddress
from pathlib import Path
import socket


class IsolationError(RuntimeError):
    pass


def parse_tcp_listeners(text: str, *, ipv6: bool, port: int = 2345) -> tuple[str, ...]:
    """Read Linux /proc/net/tcp{,6}; decode native 32-bit-little-endian fields."""
    lines = text.splitlines()
    if not lines or "local_address" not in lines[0]:
        raise IsolationError("missing /proc/net/tcp header")
    found = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 4 or ":" not in parts[1]:
            raise IsolationError("malformed TCP socket table")
        addr_hex, port_hex = parts[1].split(":", 1)
        try:
            raw = bytes.fromhex(addr_hex)
            value_port = int(port_hex, 16)
            state = int(parts[3], 16)
            if ipv6:
                if len(raw) != 16:
                    raise ValueError("invalid IPv6 length")
                normal = b"".join(raw[i:i+4][::-1] for i in range(0, 16, 4))
                address = str(ipaddress.IPv6Address(normal))
            else:
                if len(raw) != 4:
                    raise ValueError("invalid IPv4 length")
                address = str(ipaddress.IPv4Address(raw[::-1]))
        except ValueError as exc:
            raise IsolationError("invalid TCP address encoding") from exc
        if state == 0x0A and value_port == port:
            found.append(address)
    return tuple(sorted(found))


def check_no_external_interfaces(sys_net: Path) -> None:
    try:
        names = sorted(p.name for p in sys_net.iterdir())
    except OSError as exc:
        raise IsolationError("cannot inspect network interfaces") from exc
    if names != ["lo"]:
        raise IsolationError("unsafe network namespace interfaces: " + repr(names))


def inspect_network(
    *,
    interfaces: Path = Path("/sys/class/net"),
    tcp4: Path = Path("/proc/net/tcp"),
    tcp6: Path = Path("/proc/net/tcp6"),
    require_listener: bool = False,
) -> tuple[str, ...]:
    """Reject missing tables, external interfaces, absent expected GDB listeners."""
    check_no_external_interfaces(interfaces)
    try:
        ipv4 = parse_tcp_listeners(tcp4.read_text(encoding="ascii"), ipv6=False)
        ipv6 = parse_tcp_listeners(tcp6.read_text(encoding="ascii"), ipv6=True)
    except (OSError, UnicodeError) as exc:
        raise IsolationError("cannot read both IPv4 and IPv6 TCP tables") from exc
    listeners = tuple("v4:" + addr for addr in ipv4) + tuple("v6:" + addr for addr in ipv6)
    if require_listener and not listeners:
        raise IsolationError("expected GDB port listener missing or unresolved")
    # Wildcard is permitted ONLY within a separately host-verified --network none
    # namespace with precisely one interface, lo. This function alone is not
    # sufficient proof of isolation outside an independently enforced sandbox.
    return listeners


def check_no_egress(
    targets: tuple[tuple[int, tuple], ...] | None = None,
) -> None:
    """Reject any reachable endpoint; require both IP families.

    Negative connect responses alone are NOT proof of isolation: the caller
    must independently enforce Docker --network none and only-lo interfaces.
    A timeout is INCONCLUSIVE, not a verified network denial.
    """
    if targets is None:
        targets = ((socket.AF_INET, ("1.1.1.1", 443)),
                   (socket.AF_INET6, ("2606:4700:4700::1111", 443)))
    if len(targets) != 2 or {family for family, _ in targets} != {
        socket.AF_INET, socket.AF_INET6
    }:
        raise IsolationError("egress check must probe both IPv4 and IPv6")
    for family, remote in targets:
        try:
            with socket.socket(family, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.8)
                try:
                    sock.connect(remote)
                except socket.timeout as error:
                    raise IsolationError("egress probe timed out; result inconclusive") from error
                except OSError:
                    # Refusal or no route is negative connectivity evidence only.
                    continue
                raise IsolationError("external network access unexpectedly available")
        except IsolationError:
            raise
        except OSError as error:
            raise IsolationError("cannot initialize network-family egress probe") from error


if __name__ == "__main__":
    check_no_external_interfaces(Path("/sys/class/net"))
    check_no_egress()
    inspect_network()
    print("PASS: container namespace has only lo; TCP4/TCP6 readable; direct egress denied")
