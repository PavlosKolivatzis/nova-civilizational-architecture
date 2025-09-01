import slot_loader


def test_normalize_removes_leading_zeros_only():
    # leading zeros before digits are removed
    assert slot_loader.normalize("slot06") == "slot6"
    assert slot_loader.normalize("slot0001") == "slot1"
    # zeros within numbers are preserved
    assert slot_loader.normalize("slot1002") == "slot1002"

