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
bash scripts/06_taxonomy.sh          # downloads PR2 + CO1 references on first run
bash scripts/06b_blast_unknowns.sh   # NCBI BLAST (internet access required)
python3 scripts/07_build_site.py
