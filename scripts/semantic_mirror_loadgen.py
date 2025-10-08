#!/usr/bin/env python3
"""
Semantic Mirror Load Generator

Generates synthetic traffic for smoke testing and dashboard demonstrations.
Creates realistic context publication and query patterns to validate the
Semantic Mirror system under controlled load.

Usage:
    python scripts/semantic_mirror_loadgen.py --cycles 50
    python scripts/semantic_mirror_loadgen.py --delay 0.1 --verbose
"""

import argparse
import sys
import time
from typing import Dict, Any


def safe_import_semantic_mirror():
    """Import semantic mirror functions with graceful fallback."""
    try:
        from orchestrator.semantic_mirror import publish, query
        return publish, query
    except ImportError as e:
        print(f"Failed to import semantic mirror: {e}")
        print("Make sure you're running from the repo root and the orchestrator module is available.")
        sys.exit(1)


def generate_cultural_profile(iteration: int) -> Dict[str, Any]:
    """Generate synthetic cultural profile data."""
    base_adaptation = 0.5 + (iteration % 10) * 0.05  # Cycles 0.5-0.95
    return {
        "adaptation_rate": min(1.0, base_adaptation),
        "complexity_factor": 0.8 - (iteration % 5) * 0.1,  # Cycles 0.8-0.4
        "cultural_fit": 0.7 + (iteration % 3) * 0.1,  # Cycles 0.7-0.9
        "synthesis_mode": "adaptive" if iteration % 3 == 0 else "conservative",
        "iteration": iteration,
        "timestamp": time.time()
    }


def generate_production_metrics(iteration: int) -> Dict[str, Any]:
    """Generate synthetic production control metrics."""
    pressure_level = min(1.0, (iteration % 20) * 0.05)  # Cycles 0.0-0.95
    return {
        "pressure_level": pressure_level,
        "active_requests": 10 + (iteration % 15),  # Cycles 10-24
        "success_rate": max(0.7, 1.0 - pressure_level * 0.3),
        "resource_utilization": min(0.9, pressure_level + 0.2),
        "iteration": iteration
    }


def run_load_generation(cycles: int = 50, delay: float = 0.1, verbose: bool = False):
    """Run the load generation cycle."""
    publish, query = safe_import_semantic_mirror()
    
    print(f"Starting Semantic Mirror load generation: {cycles} cycles, {delay}s delay")
    
    successful_publishes = 0
    successful_queries = 0
    
    for i in range(cycles):
        try:
            # Publish Slot 6 cultural profile
            cultural_data = generate_cultural_profile(i)
            pub_result = publish(
                "slot06.cultural_profile", 
                cultural_data,
                "slot06_cultural_synthesis", 
                ttl=30.0
            )
            if pub_result:
                successful_publishes += 1
            
            # Publish Slot 7 production metrics occasionally
            if i % 5 == 0:  # Every 5th iteration
                prod_data = generate_production_metrics(i)
                pub_result = publish(
                    "slot07.public_metrics",
                    prod_data,
                    "slot07_production_controls",
                    ttl=60.0
                )
                if pub_result:
                    successful_publishes += 1
            
            # Query from Slot 3 perspective
            cultural_context = query("slot06.cultural_profile", "slot03_emotional_matrix")
            if cultural_context is not None:
                successful_queries += 1
                
                if verbose:
                    adaptation_rate = cultural_context.get("adaptation_rate", 0.0)
                    print(f"Cycle {i:3d}: Cultural adaptation={adaptation_rate:.2f}")
            
            # Query from Slot 7 perspective (some will fail due to ACL)
            if i % 3 == 0:  # Every 3rd iteration
                prod_context = query("slot07.public_metrics", "slot06_cultural_synthesis")
                if prod_context is not None:
                    successful_queries += 1
            
            # Sleep between iterations
            if delay > 0:
                time.sleep(delay)
                
        except KeyboardInterrupt:
            print(f"\nLoad generation interrupted at cycle {i}")
            break
        except Exception as e:
            if verbose:
                print(f"Error in cycle {i}: {e}")
    
    # Final summary
    total_expected_publishes = cycles + (cycles // 5)  # cultural + occasional production
    total_expected_queries = cycles + (cycles // 3)    # cultural + occasional production
    
    print("Load generation complete!")
    print(f"Publications: {successful_publishes}/{total_expected_publishes} successful")
    print(f"Queries: {successful_queries}/{total_expected_queries} successful")
    print(f"Publish success rate: {successful_publishes/total_expected_publishes*100:.1f}%")
    print(f"Query success rate: {successful_queries/total_expected_queries*100:.1f}%")
    print("loadgen_done")


def main():
    """Main load generator application."""
    parser = argparse.ArgumentParser(
        description="Semantic Mirror Load Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/semantic_mirror_loadgen.py
  python scripts/semantic_mirror_loadgen.py --cycles 100 --delay 0.05
  python scripts/semantic_mirror_loadgen.py --verbose
        """
    )
    
    parser.add_argument('--cycles', type=int, default=50,
                       help='Number of load generation cycles (default: 50)')
    parser.add_argument('--delay', type=float, default=0.1,
                       help='Delay between cycles in seconds (default: 0.1)')
    parser.add_argument('--verbose', action='store_true',
                       help='Print detailed progress information')
    
    args = parser.parse_args()
    
    try:
        run_load_generation(args.cycles, args.delay, args.verbose)
    except Exception as e:
        print(f"Load generation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()