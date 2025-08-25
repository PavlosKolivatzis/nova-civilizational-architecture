import json
import tempfile
import textwrap
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from orchestrator.plugins import PythonFilePlugin, RestAPIPlugin


def test_python_file_plugin(tmp_path: Path) -> None:
    plugin_file = tmp_path / "plugin.py"
    plugin_file.write_text(
        textwrap.dedent(
            """
            def run(x, y=0):
                return x + y
            """
        )
    )
    plugin = PythonFilePlugin(str(plugin_file))
    assert plugin.run(2, y=3) == 5


def test_rest_api_plugin() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # type: ignore[override]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

        def log_message(self, format, *args):  # pragma: no cover - silence
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        plugin = RestAPIPlugin(url)
        assert plugin.run() == {"status": "ok"}
    finally:
        server.shutdown()
        thread.join()
