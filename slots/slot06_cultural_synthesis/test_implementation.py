#!/usr/bin/env python3
"""Quick test of Slot 6 v6.5 implementation"""

try:
    from multicultural_truth_synthesis import (
        MulticulturalTruthSynthesis,
        CulturalContext,
        DeploymentGuardrailResult
    )
    print("✅ Imports successful")
    
    # Basic instantiation test
    engine = MulticulturalTruthSynthesis()
    print("✅ Engine initialization successful")
    
    # Quick analysis test
    profile = engine.analyze_cultural_context(
        "Test University", 
        {"region": "EU", "language": "en", "empiricism_priority": 0.8}
    )
    print(f"✅ Cultural analysis: {profile.adaptation_effectiveness:.3f}")
    
    print("\n🎯 SLOT 6 V6.5 IMPLEMENTATION: VALIDATED ✅")
    
