from collections import defaultdict

class PerformanceTracker:
    def __init__(self):
        self.total_processed = 0
        self.allowed = 0
        self.quarantined = 0
        self.neutralized = 0
        self.reason_code_counts = defaultdict(int)
        self.avg_processing_time = 0.0

    def update(self, processing_time_ms: float, action: str, reason_codes):
        self.total_processed += 1
        if action == "allow": self.allowed += 1
        elif action == "quarantine": self.quarantined += 1
        elif action == "neutralize": self.neutralized += 1
        for code in reason_codes or []:
            self.reason_code_counts[code] += 1
        n = self.total_processed
        self.avg_processing_time = ((self.avg_processing_time * (n - 1)) + processing_time_ms) / n
