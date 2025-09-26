#!/usr/bin/env python3
"""
Standalone Prometheus-like metrics collector for Nova.
Periodically scrapes Nova metrics and provides a simple web interface.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
from aiohttp import web
import threading

class MetricsCollector:
    def __init__(self, nova_url: str = "http://localhost:8000", scrape_interval: int = 5):
        self.nova_url = nova_url
        self.scrape_interval = scrape_interval
        self.metrics_history: List[Dict[str, Any]] = []
        self.latest_metrics: Dict[str, Any] = {}
        self.running = False

    async def scrape_metrics(self):
        """Scrape metrics from Nova endpoint"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.nova_url}/metrics") as response:
                    if response.status == 200:
                        metrics_text = await response.text()
                        metrics_data = self.parse_prometheus_metrics(metrics_text)

                        # Add timestamp
                        metrics_data['timestamp'] = time.time()
                        metrics_data['datetime'] = datetime.now().isoformat()

                        # Store in history (keep last 1000 points)
                        self.metrics_history.append(metrics_data)
                        if len(self.metrics_history) > 1000:
                            self.metrics_history.pop(0)

                        self.latest_metrics = metrics_data
                        print(f"Scraped {len(metrics_data)-2} metrics at {metrics_data['datetime']}")
                    else:
                        print(f"Failed to scrape metrics: HTTP {response.status}")
        except Exception as e:
            print(f"Error scraping metrics: {e}")

    def parse_prometheus_metrics(self, text: str) -> Dict[str, Any]:
        """Parse Prometheus format metrics into dict"""
        metrics = {}
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                if ' ' in line:
                    name_labels, value = line.rsplit(' ', 1)
                    if '{' in name_labels:
                        name, labels = name_labels.split('{', 1)
                        labels = labels.rstrip('}')
                        key = f"{name}[{labels}]"
                    else:
                        key = name_labels
                    try:
                        metrics[key] = float(value)
                    except ValueError:
                        metrics[key] = value
        return metrics

    async def collect_loop(self):
        """Main collection loop"""
        self.running = True
        print(f"Starting metrics collection from {self.nova_url}")
        print(f"Scraping every {self.scrape_interval} seconds")

        while self.running:
            await self.scrape_metrics()
            await asyncio.sleep(self.scrape_interval)

    async def metrics_handler(self, request):
        """Return latest metrics as JSON"""
        return web.json_response(self.latest_metrics)

    async def history_handler(self, request):
        """Return metrics history"""
        return web.json_response(self.metrics_history)

    async def dashboard_handler(self, request):
        """Simple web dashboard"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Nova Metrics Dashboard</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ font-family: monospace; background: #1a1a1a; color: #00ff00; padding: 20px; }}
        .metric {{ margin: 5px 0; }}
        .header {{ color: #ffff00; font-size: 1.2em; margin-bottom: 20px; }}
        .timestamp {{ color: #888; }}
        .value {{ color: #00ffff; }}
    </style>
</head>
<body>
    <div class="header">Nova Metrics Dashboard</div>
    <div class="timestamp">Last updated: {self.latest_metrics.get('datetime', 'Never')}</div>
    <div class="timestamp">Total metrics: {len(self.latest_metrics) - 2}</div>
    <br>
"""

        for key, value in sorted(self.latest_metrics.items()):
            if key not in ['timestamp', 'datetime']:
                html += f'    <div class="metric">{key}: <span class="value">{value}</span></div>\n'

        html += """
    <br>
    <div style="color: #888;">
        <a href="/api/metrics" style="color: #00ffff;">JSON API</a> |
        <a href="/api/history" style="color: #00ffff;">History</a>
    </div>
</body>
</html>"""
        return web.Response(text=html, content_type='text/html')

    def start_web_server(self, port: int = 9090):
        """Start web interface"""
        app = web.Application()
        app.router.add_get('/', self.dashboard_handler)
        app.router.add_get('/api/metrics', self.metrics_handler)
        app.router.add_get('/api/history', self.history_handler)

        print(f"Web dashboard starting on http://localhost:{port}")
        web.run_app(app, host='0.0.0.0', port=port)

async def main():
    collector = MetricsCollector()

    # Start collection in background
    collection_task = asyncio.create_task(collector.collect_loop())

    # Start web server in thread to avoid blocking
    def run_web():
        collector.start_web_server()

    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()

    try:
        await collection_task
    except KeyboardInterrupt:
        print("Stopping metrics collector...")
        collector.running = False

if __name__ == "__main__":
    asyncio.run(main())