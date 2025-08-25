import os
import subprocess
import sys


def test_similar_deterministic_across_runs():
    code = """
import json
from frameworks.geometric_memory import GeometricMemory
gm = GeometricMemory(enabled=True)
gm.put('alpha', 1)
gm.put('beta', 2)
gm.put('gamma', 3)
print(json.dumps(gm.similar('alpha', k=2)))
"""

    def run(seed: int) -> bytes:
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = str(seed)
        return subprocess.check_output([sys.executable, "-c", code], env=env)

    out1 = run(1)
    out2 = run(2)
    assert out1 == out2
