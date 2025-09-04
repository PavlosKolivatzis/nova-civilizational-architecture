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
