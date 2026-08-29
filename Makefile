PYTHON ?= .venv/bin/python
REPOS ?= pallets/flask psf/requests numpy/numpy
GH_HOUR ?=
TRAVIS_FILE ?=

.PHONY: setup objective1-snapshot collect-real-corpus objective1-real objective1 objective1-report objective1-paper-pack objective1-paper-pack-pdf objective1-merge objective1-gharchive objective1-travis all-pocs

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

# Reproduce the frozen 3,000-run GitHub Actions snapshot (no network).
objective1-snapshot:
	$(PYTHON) src/analysis/objective1_parameter_analysis.py --infile data/processed/unified_build_dataset.csv --outdir outputs/objective1_real
	$(PYTHON) src/analysis/association_pvalue_correction.py --infile outputs/objective1_real/parameter_association.csv --outfile outputs/objective1_real/parameter_association_corrected.csv
	$(PYTHON) src/analysis/objective1_temporal_analysis.py --infile data/processed/unified_build_dataset.csv --outdir outputs/objective1_temporal_real
	$(PYTHON) src/analysis/objective1_robustness_analysis.py --infile data/processed/unified_build_dataset.csv --outdir outputs/objective1_robustness_real
	@echo "[OK] Reproduced Objective 1 analyses. See outputs/objective1_real/"

# Re-collect live public GitHub Actions traces (requires GITHUB_TOKEN).
collect-real-corpus:
	$(PYTHON) src/collect/collect_real_multirepo.py
	$(PYTHON) src/schema/unify_schema.py --inputs $(wildcard data/raw/real/*.csv) --out data/processed/unified_build_dataset.csv

objective1:
	$(PYTHON) src/collect/github_actions_collector.py --repos $(REPOS) --max-runs-per-repo 60
	$(PYTHON) src/schema/unify_schema.py --infile data/raw/github_actions_raw.csv
	$(PYTHON) src/analysis/objective1_parameter_analysis.py

objective1-travis:
ifeq ($(strip $(TRAVIS_FILE)),)
	@echo "TRAVIS_FILE is required. Example: make objective1-travis TRAVIS_FILE=/path/to/travistorrent.csv"
else
	$(PYTHON) src/collect/travistorrent_collector.py --infile "$(TRAVIS_FILE)"
endif

objective1-gharchive:
ifeq ($(strip $(GH_HOUR)),)
	@echo "GH_HOUR is required. Example: make objective1-gharchive GH_HOUR=2025-01-01-0"
else
	$(PYTHON) src/collect/gharchive_collector.py --hour $(GH_HOUR) --repos $(REPOS)
endif

objective1-merge:
	$(PYTHON) src/schema/unify_schema.py --inputs data/raw/github_actions_raw.csv data/raw/travistorrent_raw.csv data/raw/gharchive_raw.csv
	$(PYTHON) src/analysis/objective1_parameter_analysis.py

objective1-report:
	$(PYTHON) src/analysis/export_objective1_report.py

objective1-real: objective1 objective1-report
	@echo "[OK] Objective 1 real workflow complete. See outputs/objective1/"

objective1-paper-pack: objective1-real
	$(PYTHON) src/analysis/build_objective1_paper_pack.py
	@echo "[OK] Objective 1 thesis paper pack created at outputs/objective1/paper_pack/"

objective1-paper-pack-pdf: objective1-paper-pack
	$(PYTHON) src/analysis/export_objective1_paper_pack_pdf.py
	@echo "[OK] Objective 1 paper pack PDF created at outputs/objective1/paper_pack/objective1_results_section.pdf"

all-pocs:
	$(PYTHON) run_all_pocs.py
