from nova.slots.slot05_constellation.constellation_engine import ConstellationEngine


def test_connectivity_across_components():
    engine = ConstellationEngine()
    constellation = [{"id": 0}, {"id": 1}, {"id": 2}]
    # only a link between first two items -> one component plus isolated node
    links = [
        {"source": 0, "target": 1, "strength": 0.5, "type": "conceptual", "bidirectional": True}
    ]
    partial = engine._calculate_connectivity(constellation, links)
    assert 0 <= partial < 1.0

    # add link connecting last item to form single component
    links.append({"source": 1, "target": 2, "strength": 0.5, "type": "conceptual", "bidirectional": True})
    full = engine._calculate_connectivity(constellation, links)
    assert full > partial
    assert full <= 1.0
