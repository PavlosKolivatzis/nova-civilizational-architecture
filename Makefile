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

arc-ablation:
	@echo "Running ablation studies..."
	@for ablation in spectral equilibrium shield; do \
		echo "=== Ablation: $$ablation ==="; \
		for i in $$(seq 1 5); do \
			python src/nova/arc/run_calibration_cycle.py \
				--cycle $$i \
				--domains $(DOMAINS) \
				--ablate $$ablation \
				--output data/arc_cycle_$${i}_ablate_$${ablation}_results.json || exit 1; \
		done; \
		python src/nova/arc/analyze_results.py \
			--results-dir data/ \
			--glob "arc_cycle_*_ablate_$${ablation}_results.json" \
			--output docs/reports/arc_ablation_$${ablation}_analysis.md; \
	done

arxiv-pdf:
	@echo "Generating arXiv-ready PDF..."
	@cd docs/papers && \
	pdflatex universal_structure_mathematics_arxiv.tex && \
	bibtex universal_structure_mathematics_arxiv && \
	pdflatex universal_structure_mathematics_arxiv.tex && \
	pdflatex universal_structure_mathematics_arxiv.tex && \
	mv universal_structure_mathematics_arxiv.pdf ../../../universal_structure_mathematics.pdf
	@echo "PDF generated: universal_structure_mathematics.pdf"

arc-verify:
	python scripts/verify_vault.py-e 
# Navigation and Development Targets
.PHONY: nav tree docs test-quick setup

nav: ## Show repository navigation guide
	@cat docs/NAVIGATION.md

tree: ## Show visual directory tree
	@cat TREE.md

docs: ## Open documentation in browser
	@python3 -c "import webbrowser; webbrowser.open('docs/README.md')"

test-quick: ## Run health tests only (fast)
	@pytest -m health -q --tb=short

setup: ## Bootstrap development environment
	@./scripts/bootstrap_dev_env.sh
