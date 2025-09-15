from __future__ import annotations
from slots.slot10_civilizational_deployment.core import SnapshotBackout

def test_cross_slot_rollback():
    backout = SnapshotBackout()
    bundle = backout.record_promotion(slot10_id="s10_A", slot08_id="s8_B", slot04_id="s4_C")

    called = {"s10": [], "s8": [], "s4": []}
    def app_restore(i): called["s10"].append(i); return True
    def s8_restore(i): called["s8"].append(i); return True
    def s4_restore(i): called["s4"].append(i); return True

    ok = backout.rollback(app_restore, s8_restore, s4_restore)
    assert ok is True
    assert called["s10"] == [bundle.slot10_id]
    assert called["s8"] == [bundle.slot08_id]
    assert called["s4"] == [bundle.slot04_id]