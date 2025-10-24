.PHONY: arc-baseline arc-cycles arc-stability arc-analyze reproduce-arc-experiment arc-verify

SEED ?= 1337
DOMAINS ?= data/arc_baseline_domains.json
RESULTS ?= data/arc_baseline_results.json

arc-baseline:
	python scripts/generate_arc_test_domains.py --seed $(SEED) --count 100 --output $(DOMAINS)
	python scripts/arc_baseline_sweep.py --domains $(DOMAINS) --output $(RESULTS)
	python scripts/arc_analyze_baseline.py --results $(RESULTS) --output docs/reports/arc_baseline_analysis.md

arc-cycles:
	@for i in $$(seq 1 10); do \
		echo "=== ARC Calibration Cycle $$i ==="; \
		python scripts/arc_calibration_cycle.py \
			--cycle $$i \
			--domains $(DOMAINS) \
			--previous data/arc_cycle_$$(($$i-1))_results.json \
			--output data/arc_cycle_$${i}_results.json || exit 1; \
		python scripts/verify_vault.py >> logs/arc_calibration_audit.log; \
	done

arc-stability:
	python scripts/arc_stability_monitor.py \
		--duration 604800 \
		--interval 3600 \
		--domains $(DOMAINS) \
		--output data/arc_stability_results.json

arc-analyze:
	python src/nova/arc/analyze_results.py --cycles 10 --glob "data/arc_cycle_*_results.json" \
		--stability data/arc_stability_results.json \
		--out-md docs/reports/arc_experiment_final.md \
		--out-json data/arc_final_results.json

reproduce-arc-experiment: arc-baseline arc-cycles arc-stability arc-analyze

arc-verify:
	python scripts/verify_vault.py