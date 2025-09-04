from slots.slot02_deltathresh.patterns import compile_detection_patterns

def test_patterns_compile():
    pats = compile_detection_patterns()
    assert all(layer in pats for layer in ("delta","sigma","theta","omega"))
    assert all(len(pats[layer]) >= 2 for layer in pats)
