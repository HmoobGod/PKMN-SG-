#!/usr/bin/env python3
"""GENERATED-ROM ONLY strict RSP stop adapter, never called by run_capture().

Uses PR26's exact original RSP ACK/frame receiver and PR41 opt-in qSupported.
Does NOT install any breakpoints, change the original game controller, or
supply a private ROM/save path. The caller is a disposable public test harness.
"""
from __future__ import annotations
import socket
from capture_original_request_rsp import (
    RSP, parse_registers, require, strict_public_negotiated_stop,
)

GENERATED_THUMB_PC = 0x08000100
ALLOWED_GENERATED_PCS = frozenset(
    (GENERATED_THUMB_PC, GENERATED_THUMB_PC + 2, GENERATED_THUMB_PC + 4)
)


class PublicStrictStopAdapter:
    """One-use generated-only continue; no breakpoints, no public CLI."""

    def __init__(self, rsp: RSP):
        require(type(rsp) is RSP, "adapter requires exact PR26 RSP instance")
        self.rsp = rsp
        self._one_use = False

    def negotiate(self) -> bytes:
        require(not self._one_use, "generated fixture adapter already consumed")
        return self.rsp.negotiate_public_breakpoint_capabilities()

    def one_generated_stop(self, *, timeout: float = 3.0) -> int:
        rsp = self.rsp
        require(type(timeout) in (float, int) and 0 < timeout <= 3,
                "bounded generated fixture timeout required")
        require(not self._one_use and rsp._features_negotiated and
                not rsp._feature_negotiation_failed and not rsp.running,
                "must negotiate fresh public capabilities before one continue")
        self._one_use = True  # one-use even when send ACK or stop fails
        saved_timeout = rsp.sock.gettimeout()
        try:
            rsp.sock.settimeout(timeout)
            try:
                rsp._transmit("c")
            finally:
                # ACK may be missing even after emulator starts running.
                rsp.running = True
            stop_bytes = rsp.receive()
            strict_public_negotiated_stop(stop_bytes)
            rsp.running = False  # ONLY after canonical exact T05hwbreak:;
            registers = parse_registers(rsp.send("g"))
            pc = registers[15]
            require(pc in ALLOWED_GENERATED_PCS,
                    "generated-only poststop PC is not the Thumb target")
            return pc
        except BaseException:
            # Do not leave this adapter able to install/remove breakpoints
            # or issue any read after a bad/unknown stop or a bad PC.
            # Caller must terminate the disposable emulator process.
            rsp._feature_negotiation_failed = True
            rsp.running = True
            raise
        finally:
            rsp.sock.settimeout(saved_timeout)


if __name__ == "__main__":
    raise SystemExit("generated-only source adapter; no CLI or private capture")
