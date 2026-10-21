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
Rscript scripts/08_diversity.R
Rscript scripts/09_ecology.R
bash scripts/10_protein_search.sh    # translates the CO1 reference on first run
bash scripts/11_rotifer_index.sh
Rscript scripts/12_manuscript.R
python3 scripts/13_sra_prep.py
python3 scripts/14_verify_references.py   # Crossref (internet access required)
Rscript scripts/15_microscopy_comparison.R
Rscript scripts/12_manuscript.R           # again, to include the microscopy comparison
python3 scripts/99_build_site.py
