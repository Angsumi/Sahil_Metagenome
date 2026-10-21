#!/usr/bin/env bash
# Step 11 — Rotifer trophic index (QB/T, Sládeček 1983): number of Brachionus species divided
# by number of Trichocerca species. Because few COI sequences can be named to species, species
# are approximated by MOTUs: COI ASVs clustered at 97 % identity (a common COI species proxy).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=results/11_rotifer_index
mkdir -p "$OUT"

# Abundance-sorted clustering needs ;size= annotations: use total reads per ASV
awk -F'\t' 'NR==FNR { if (FNR > 1) size[$1] = $2 + $3; next }
            /^>/ { id = substr($1, 2); print ">" id ";size=" size[id]; next } { print }' \
  results/04_curation/COI_asv_table_curated.tsv results/04_curation/COI_asv_seqs_curated.fasta \
  > work/coi_sized.fasta
vsearch --cluster_size work/coi_sized.fasta --id 0.97 --sizein --strand plus \
  --uc "$OUT/COI_motu97.uc" --quiet

Rscript scripts/11_rotifer_index.R
