#!/usr/bin/env bash
# Run the full processing pipeline end to end, then rebuild the GitHub Pages site.
# Requires the conda environment in environment.yml:
#   micromamba create -f environment.yml && micromamba activate metabar
set -euo pipefail
cd "$(dirname "$0")/.."

bash scripts/01_qc.sh
bash scripts/02_primer_removal.sh
#                             marker truncF truncR maxEE_F maxEE_R
Rscript scripts/03_dada2.R    18S    270    210    2       4
Rscript scripts/03_dada2.R    COI    250    200    2       4
Rscript scripts/04_asv_curation.R
Rscript scripts/05_summary.R
python3 scripts/06_build_site.py
