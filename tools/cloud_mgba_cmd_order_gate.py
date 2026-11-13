#!/usr/bin/env python3
"""Static fail-closed check of the PUBLIC mGBA lab Dockerfile CMD.

Runs on the GitHub host against the exact Dockerfile copied to build context,
before docker build or any emulator. No game inputs, network or subprocesses.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

EXPECTED_STAGES = (
    "python3 /lab/tools/cloud_mgba_pkg_gate.py",
    "mgba --version",
    "sha256sum $(command -v mgba)",
    "python3 -m unittest discover -s /lab/tools -p 'test_*.py' -v",
    "xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_combined_fixture.py",
    "xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb2_fixture.py",
    "timeout -k 3s 50s xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb_hit_fixture.py",
    "timeout -k 3s 50s xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb_qsupported_fixture.py",
)


# Full exact Dockerfile pin: Docker instructions are case-insensitive, may be
# overridden by a later CMD / ENTRYPOINT / FROM, and can modify effective USER
# or COPY. Only a complete-file equality check guarantees this property.
EXPECTED_DOCKERFILE = (
    "FROM ubuntu:26.04\n"
    "ENV DEBIAN_FRONTEND=noninteractive\n"
    "RUN apt-get update -qq && apt-get install --no-install-recommends -y python3 mgba-sdl xvfb xauth && rm -rf /var/lib/apt/lists/*\n"
    "ENV PATH=\"/usr/games:${PATH}\"\n"
    "WORKDIR /lab\n"
    "COPY tools /lab/tools\n"
    "ENV PYTHONDONTWRITEBYTECODE=1\n"
    "ENV HOME=/tmp\n"
    "USER 65534:65534\n"
    "CMD [\"sh\",\"-c\",\"python3 /lab/tools/cloud_mgba_pkg_gate.py && mgba --version && sha256sum $(command -v mgba) && python3 -m unittest discover -s /lab/tools -p 'test_*.py' -v && xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_combined_fixture.py && xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb2_fixture.py && timeout -k 3s 50s xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb_hit_fixture.py && timeout -k 3s 50s xvfb-run -a -s '-screen 0 640x480x24' python3 /lab/tools/cloud_rsp_thumb_qsupported_fixture.py\"]\n"
)


def validate_dockerfile(text: str) -> tuple[str, ...]:
    if type(text) is not str:
        raise ValueError("Dockerfile text must be UTF-8")
    if text != EXPECTED_DOCKERFILE:
        actual_lines = text.splitlines(keepends=True)
        expected_lines = EXPECTED_DOCKERFILE.splitlines(keepends=True)
        for index in range(max(len(actual_lines), len(expected_lines))):
            observed = actual_lines[index] if index < len(actual_lines) else None
            expected = expected_lines[index] if index < len(expected_lines) else None
            if observed != expected:
                raise ValueError(f"Dockerfile mismatch at line {index + 1} (full-file pin)")
        raise ValueError("Dockerfile exact-text mismatch")
    commands = [line[4:] for line in text.splitlines() if line.startswith("CMD ")]
    if len(commands) != 1:
        raise ValueError("expected exactly one JSON-form Docker CMD")
    try:
        command = json.loads(commands[0])
    except (ValueError, TypeError) as error:
        raise ValueError("malformed Docker CMD JSON") from error
    if not isinstance(command, list) or command[:2] != ["sh", "-c"] or len(command) != 3:
        raise ValueError("CMD must be exactly sh -c and one command string")
    script = command[2]
    if type(script) is not str or any(x in script for x in (";", "|", "\n", "\r", "\x00")):
        raise ValueError("forbidden shell syntax in Docker CMD")
    steps = tuple(script.split(" && "))
    if steps != EXPECTED_STAGES:
        raise ValueError("Docker CMD exact gate-first pipeline and fixtures do not match")
    return steps


def main() -> None:
    if len(sys.argv) != 2:
        raise ValueError("exactly one public Dockerfile argument required")
    source = Path(sys.argv[1])
    if source.is_symlink() or not source.is_file():
        raise ValueError("regular nonsymlink Dockerfile required")
    validated = validate_dockerfile(source.read_text(encoding="utf-8"))
    print(f"PUBLIC_DOCKER_CMD_ORDER: PASS gate_first={validated[0]} stages={len(validated)}")


if __name__ == "__main__":
    main()
