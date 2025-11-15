# ruff: noqa: E402
from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova import slot_loader


def test_normalize_removes_leading_zeros_only():
    # leading zeros before digits are removed
    assert slot_loader.normalize("slot06") == "slot6"
    assert slot_loader.normalize("slot0001") == "slot1"


def test_normalize_preserves_mid_number_zeros():
    # zeros within numbers are preserved
    assert slot_loader.normalize("slot1002") == "slot1002"
    assert slot_loader.normalize("slot60007") == "slot60007"
