#!/usr/bin/env python3
"""Real public mGBA synthetic-ROM RSP inside host-verified Docker --network none."""
from __future__ import annotations
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
from cloud_mgba_rsp_fixture import HOST, PORT, check_reply, make_fixture, request
from cloud_rsp_netns_gate import check_no_egress, inspect_network

def main():
    if os.environ.get("SOULGOLD_ALLOW_PRIVATE_INPUTS"):
        raise RuntimeError("private-game opt-in forbidden")
    # Before any emulator is launched, fail closed on BOTH v4/v6 and link state.
    initial=inspect_network()
    check_no_egress()
    print("NETWORK_BEFORE_MGBA: only-lo; no IPv4/IPv6 direct egress")
    with tempfile.TemporaryDirectory(prefix="sg-public-netns-") as tmp:
        root=Path(tmp)
        image=root/"public_original_fixture.gba"
        image.write_bytes(make_fixture())
        image.chmod(0o600)
        home=root/"home"; home.mkdir(mode=0o700)
        env={k:os.environ[k] for k in ("PATH","DISPLAY","XAUTHORITY") if k in os.environ}
        env.update(HOME=str(home),SDL_AUDIODRIVER="dummy")
        p=subprocess.Popen(["mgba","-g",str(image)],
                           cwd=root,env=env,stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=time.monotonic()+25
            client=None
            while time.monotonic()<deadline:
                if p.poll() is not None:
                    raise RuntimeError("mGBA exited before loopback listener")
                try:
                    client=socket.create_connection((HOST,PORT),timeout=1)
                    break
                except OSError:
                    time.sleep(0.25)
            if client is None:
                raise RuntimeError("no local mGBA listener in isolated container")
            with client:
                client.settimeout(5)
                listeners=inspect_network(require_listener=True)
                check_no_egress()
                stop=request(client,b"?")
                regs=request(client,b"g")
                memory=request(client,b"m080000c0,4")
                check_reply(stop,regs,memory)
            print("REAL_SYNTHETIC_RSP: PASS, ?/g/m only, no execution control")
            print("GDB_LISTENERS_INSIDE_ISOLATED_NAMESPACE: "+repr(listeners))
            print("STOP: "+stop.decode("ascii"))
            print("REGISTER_BYTES: "+str(len(regs)//2))
            print("ROM_REPLY: "+memory.decode("ascii"))
            print("NATIVE_SOULGOLD_ACCEPTANCE: 0/20; no private ROM/save")
        finally:
            if p.poll() is None: p.terminate()
            try: p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill();p.wait(timeout=3)

if __name__=="__main__":
    main()
