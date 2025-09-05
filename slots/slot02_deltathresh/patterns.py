import re
from typing import Dict, List, Pattern

def compile_detection_patterns() -> Dict[str, List[Pattern]]:
    return {
        'delta': [
            re.compile(r'\bundeniable\s+truth\b', re.I),
            re.compile(r'\bcannot\s+be\s+(?:questioned|disputed|denied)\b', re.I),
            re.compile(r'\bself-evident\s+(?:truth|fact)\b', re.I),
        ],
        'sigma': [
            re.compile(r'\bofficial\s+(?:statement|position|policy)\b', re.I),
            re.compile(r'\bauthoritative\s+(?:source|voice|guidance)\b', re.I),
        ],
        'theta': [
            re.compile(r'\bas\s+(?:proven|established)\s+(?:above|earlier)\b', re.I),
            re.compile(r'\bthis\s+(?:proves|validates)\s+our\s+(?:point|claim)\b', re.I),
        ],
        'omega': [
            re.compile(r'\beveryone\s+(?:knows|agrees|believes)\b', re.I),
            re.compile(r'\bwidely\s+(?:accepted|believed|known)\b', re.I),
            re.compile(r'\bviral\s+truth\b', re.I),
        ],
    }

ABSOLUTE = re.compile(r'\b(always|never|everyone|nobody|undeniably|absolutely|certainly)\b', re.I)
HUMILITY = re.compile(r'\b(may|might|could|appears|suggests|evidence|source|study|data|research)\b', re.I)
UNCERTAINTY = re.compile(r'\b(uncertain|unclear|unknown|possibly|perhaps|seems)\b', re.I)


class PatternDetector:
    """Analyze and neutralize manipulation patterns."""

    def __init__(self, config=None):
        self.patterns = compile_detection_patterns()

    def detect_patterns(self, content: str) -> Dict[str, float]:
        words = max(1, len(content.split()))
        scores: Dict[str, float] = {}
        for layer, pats in self.patterns.items():
            total = sum(len(p.findall(content)) for p in pats)
            density = total / words
            scores[layer] = min(1.0, density * 5.0)
        return scores

    def analyze_tri_patterns(self, content: str) -> Dict[str, int]:
        return {
            'absolute_claims': len(ABSOLUTE.findall(content)),
            'humility_indicators': len(HUMILITY.findall(content)),
            'uncertainty_acknowledgments': len(UNCERTAINTY.findall(content)),
        }

    def neutralize_patterns(self, content: str) -> str:
        result = content
        for pats in self.patterns.values():
            for p in pats:
                result = p.sub("[REDACTED]", result)
        return result

    def validate_patterns(self) -> Dict[str, int]:
        return {layer: len(pats) for layer, pats in self.patterns.items()}
