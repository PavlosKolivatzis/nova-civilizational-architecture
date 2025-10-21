#!/usr/bin/env python
import json, math, time, hashlib, random
NODES = ["n1","n2","n3","n4","n5"]

def vote(node_id):
    # toy alignment & provenance demo
    alignment = max(0.0, min(1.0, random.gauss(0.86, 0.06)))
    prov = 1.0
    w = 1.0
    sig = hashlib.sha256(f"{node_id}:{alignment}".encode()).hexdigest()[:16]
    return {"node_id": node_id, "weight": w, "alignment": alignment,
            "provenance_integrity": prov, "signature": sig}

def fcq(votes):
    num = sum(v["weight"]*v["alignment"]*v["provenance_integrity"] for v in votes)
    den = sum(v["weight"] for v in votes) or 1.0
    return num/den

def main():
    votes = [vote(n) for n in NODES]
    q = fcq(votes)
    decision = {
        "id": "demo-001",
        "topic": "deploy_phase10_cityA",
        "threshold": 0.90,
        "fcq": round(q, 3),
        "votes": votes,
        "decay_recheck_after_hours": 72,
        "provenance": {
            "hash": hashlib.sha256(json.dumps(votes).encode()).hexdigest(),
            "parent_hash": "link-to-phase9",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }
    print(json.dumps(decision, indent=2))

if __name__ == "__main__":
    main()
