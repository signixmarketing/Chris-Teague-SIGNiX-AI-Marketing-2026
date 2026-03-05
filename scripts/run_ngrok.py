#!/usr/bin/env python3
"""
Start ngrok and keep it running until interrupted (SIGINT/SIGTERM).
Used by Cursor/VS Code "Django with ngrok" compound launch so stopping
debugging also stops ngrok.

Requires:
  - ngrok on PATH
  - NGROK_DOMAIN set to your full domain hostname (e.g. something.ngrok-free.dev)
  - Optional: NGROK_PORT (default 8000)
"""

import os
import signal
import subprocess
import sys

DOMAIN = os.environ.get("NGROK_DOMAIN", "").strip()
PORT = os.environ.get("NGROK_PORT", "8000").strip()

if not DOMAIN:
    print("NGROK_DOMAIN is not set. Set it to your ngrok domain (e.g. something.ngrok-free.dev).", file=sys.stderr)
    sys.exit(1)

def main():
    proc = subprocess.Popen(
        ["ngrok", "http", "--domain", DOMAIN, PORT],
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    def shutdown(signum=None, frame=None):
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    proc.wait()
    sys.exit(proc.returncode or 0)


if __name__ == "__main__":
    main()
