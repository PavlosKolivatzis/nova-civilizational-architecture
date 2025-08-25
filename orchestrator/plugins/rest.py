from __future__ import annotations

import json
from typing import Any, Dict, Optional
from urllib import request


class RestAPIPlugin:
    """Simple REST API helper plugin.

    This plugin performs a request against the configured ``url`` when
    :meth:`run` is invoked.  If ``data`` is provided, a JSON payload is sent
    using the configured HTTP method.  The response is parsed as JSON when
    possible, falling back to raw text otherwise.
    """

    def __init__(self, url: str, method: str = "GET", timeout: float = 5.0) -> None:
        self.url = url
        self.method = method.upper()
        self.timeout = timeout

    def run(self, data: Optional[Dict[str, Any]] = None) -> Any:
        headers: Dict[str, str] = {}
        body: Optional[bytes] = None
        if data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
        req = request.Request(self.url, data=body, headers=headers, method=self.method)
        with request.urlopen(req, timeout=self.timeout) as resp:
            content = resp.read()
            try:
                return json.loads(content)
            except Exception:
                return content.decode()
