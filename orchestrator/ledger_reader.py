"""Read-only ledger status reader for federation correlation."""

import json
import os
import subprocess
import time
from typing import Dict
from urllib import request
from urllib.error import URLError


def get_ledger_status(timeout: float = 2.0) -> Dict[str, float]:
    """
    Fetch ledger height and head age from configured source.

    Returns {"height": int, "head_age": float} on success,
    or {"height": 0, "head_age": 0.0} on error (non-fatal).

    Reads one of:
      NOVA_LEDGER_STATUS_URL  (HTTP JSON: {"height": int, "head_ts": unix})
      NOVA_LEDGER_STATUS_CMD  (shell emits same JSON)
    """
    url = os.getenv("NOVA_LEDGER_STATUS_URL", "").strip()
    cmd = os.getenv("NOVA_LEDGER_STATUS_CMD", "").strip()

    if url:
        try:
            req = request.Request(url, headers={"Accept": "application/json"})
            with request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                height = int(data.get("height", 0))
                head_ts = float(data.get("head_ts", 0.0))
                head_age = max(0.0, time.time() - head_ts) if head_ts > 0 else 0.0
                return {"height": height, "head_age": head_age}
        except (URLError, json.JSONDecodeError, ValueError, KeyError):
            pass

    if cmd:
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                height = int(data.get("height", 0))
                head_ts = float(data.get("head_ts", 0.0))
                head_age = max(0.0, time.time() - head_ts) if head_ts > 0 else 0.0
                return {"height": height, "head_age": head_age}
        except (subprocess.TimeoutExpired, json.JSONDecodeError, ValueError, KeyError):
            pass

    return {"height": 0, "head_age": 0.0}
