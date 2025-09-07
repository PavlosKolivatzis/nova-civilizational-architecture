#!/usr/bin/env python3
"""
Debug script for Slot 3 negation bug analysis
============================================

Tests the negation window bug reported in GitHub issue.
The bug: negation only affects the first sentiment token, not all tokens in the window.
"""

from slots.slot03_emotional_matrix.emotional_matrix_engine import EmotionalMatrixEngine, EmotionConfig

def test_negation_bug():
    """Comprehensive test of the negation bug."""
    
    print("SLOT 3 NEGATION BUG ANALYSIS")
    print("=" * 50)
    
    engine = EmotionalMatrixEngine()
    print(f"Engine Version: {engine.__version__}")
    print(f"Negation Window: {engine.cfg.negation_window}")
    print()
    
    # Test cases that should ALL be negative but aren't due to the bug
    test_cases = [
        # Basic cases - window size 3 should cover multiple words
        ("not good", "Should be negative: only 'good' negated"),
        ("not good great", "Should be negative: both 'good' and 'great' negated"),
        ("not good great wonderful", "Should be negative: all 3 words negated"),
        ("not good great wonderful amazing", "Should be mixed: only first 3 negated"),
        
        # Different negators
        ("never happy excited", "Should be negative: 'never' negates 2 words"),
        ("don't love hate", "Should be very negative: negated love + hate"),
        ("cannot good bad", "Should be neutral-ish: negated good cancels bad"),
        
        # Edge cases
        ("not", "Should be neutral: no sentiment to negate"),
        ("good not", "Should be positive: 'not' after sentiment"),
        ("not not good", "Should be positive: double negation"),
    ]
    
    print("TEST RESULTS:")
    print("-" * 80)
    print(f"{'Test Case':<25} {'Tone':<10} {'Score':<8} {'Expected':<12} {'Status'}")
    print("-" * 80)
    
    bug_count = 0
    
    for text, expectation in test_cases:
        result = engine.analyze(text)
        tone = result['emotional_tone']
        score = result['score']
        
        # Determine if this is behaving as expected
        status = "OK"
        if "Should be negative" in expectation and tone != "negative":
            status = "BUG"
            bug_count += 1
        elif "Should be positive" in expectation and tone != "positive":
            status = "BUG" 
            bug_count += 1
        elif "Should be neutral" in expectation and tone != "neutral":
            status = "CHECK"
            
        print(f"{text:<25} {tone:<10} {score:>7.3f} {expectation.split(':')[0]:<12} {status}")
        
        # Show detailed breakdown for bug cases
        if status == "BUG":
            explain = result['explain']
            print(f"  -> Details: pos={explain['pos_strength']}, neg={explain['neg_strength']}, matched={explain['matched']}")
    
    print("-" * 80)
    print(f"BUGS FOUND: {bug_count}")
    print()
    
    # Demonstrate the exact bug mechanism
    print("BUG MECHANISM ANALYSIS:")
    print("-" * 30)
    
    # This should help visualize what's happening
    test_text = "not good great wonderful"
    result = engine.analyze(test_text)
    
    print(f"Input: '{test_text}'")
    print(f"Expected: All 3 sentiment words negated -> negative tone")
    print(f"Actual: {result['emotional_tone']} tone (score: {result['score']:.3f})")
    print(f"Breakdown: pos_strength={result['explain']['pos_strength']}, neg_strength={result['explain']['neg_strength']}")
    print()
    print("EXPLANATION:")
    print("   The bug is in lines 133-137 of emotional_matrix_engine.py")
    print("   The 'break' statement exits the negation window after the first match,")
    print("   so 'good' gets negated but 'great' and 'wonderful' remain positive.")
    print()
    
    return bug_count

def test_window_size_impact():
    """Test how different window sizes affect the bug."""
    print("WINDOW SIZE IMPACT TEST:")
    print("-" * 30)
    
    test_text = "not good great wonderful amazing fantastic"
    
    for window_size in [1, 2, 3, 5, 10]:
        config = EmotionConfig(negation_window=window_size)
        engine = EmotionalMatrixEngine(config)
        result = engine.analyze(test_text)
        
        print(f"Window {window_size}: {result['emotional_tone']} (score: {result['score']:.3f})")
    
    print()

if __name__ == "__main__":
    bugs_found = test_negation_bug()
    test_window_size_impact()
    
    print("CONCLUSION:")
    print(f"   The negation bug affects {bugs_found} test cases.")
    print("   Fix required: Remove 'break' statement and continue processing tokens in window.")
    print("   This is a HIGH PRIORITY bug affecting core sentiment analysis accuracy.")