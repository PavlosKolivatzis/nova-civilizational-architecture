from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

@dataclass
class ProcessingResult:
    content: str
    action: str  # 'allow' | 'quarantine' | 'neutralize'
    reason_codes: List[str]
    tri_score: float
    layer_scores: Dict[str, float]
    processing_time_ms: float
    content_hash: str
    neutralized_content: Optional[str] = None
    quarantine_reason: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    operational_mode: Optional[str] = None
    session_id: str = "default"
    anchor_integrity: float = 1.0
