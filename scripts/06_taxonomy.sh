#!/usr/bin/env bash
# Step 6 — Taxonomic assignment of curated ASVs with VSEARCH.
#  (a) SINTAX: k-mer classifier with bootstrap confidence per rank (cutoff applied in R).
#  (b) Global alignment to the same reference: % identity of the closest reference sequence,
#      used to decide whether genus/species names are close enough to trust.
# References (downloaded to work/refs, git-ignored):
#   18S : PR2 v5.1.1 SSU, UTAX/SINTAX format
#         https://github.com/pr2database/pr2database/releases/tag/v5.1.1
#   COI : Eukaryote CO1 Reference Set v5.1.0 (Porter & Hajibabaei), SINTAX format
#         https://github.com/terrimporter/CO1Classifier/releases/tag/SINTAX-COI-v5.1.0-ref
set -euo pipefail
cd "$(dirname "$0")/.."

REFS=work/refs
OUT=results/06_taxonomy
mkdir -p "$REFS" "$OUT"

if [ ! -s "$REFS/pr2_5.1.1_UTAX.fasta.gz" ]; then
  curl -sL -o "$REFS/pr2_5.1.1_UTAX.fasta.gz" \
    https://github.com/pr2database/pr2database/releases/download/v5.1.1/pr2_version_5.1.1_SSU_UTAX.fasta.gz
fi
if [ ! -s "$REFS/COIv5.1.0_sintax.fasta" ]; then
  curl -sL -o "$REFS/coi.zip" \
    https://github.com/terrimporter/CO1Classifier/releases/download/SINTAX-COI-v5.1.0-ref/SINTAX_COIv5.1.0_ref.zip
  # sequences are distributed in lower case, which VSEARCH treats as masked -> upper-case them
  unzip -p "$REFS/coi.zip" training/sintax.fasta | awk '/^>/ {print; next} {print toupper($0)}' \
    > "$REFS/COIv5.1.0_sintax.fasta" && rm "$REFS/coi.zip"
fi

declare -A DB=( [18S]="$REFS/pr2_5.1.1_UTAX.fasta.gz" [COI]="$REFS/COIv5.1.0_sintax.fasta" )

for m in 18S COI; do
  q=results/04_curation/${m}_asv_seqs_curated.fasta
  # (a) classifier, 100 bootstrap subsamples, both strands
  vsearch --sintax "$q" --db "${DB[$m]}" --strand both --sintax_random --randseed 2026 \
    --tabbedout "$OUT/${m}_sintax.tsv" --threads 16 --quiet
  # (b) closest reference sequence (top hits only; ties kept)
  vsearch --usearch_global "$q" --db "${DB[$m]}" --id 0.70 --strand both \
    --maxaccepts 20 --maxrejects 500 --top_hits_only --output_no_hits \
    --userout "$OUT/${m}_tophit.tsv" --userfields query+target+id+alnlen \
    --threads 16 --quiet
done

Rscript scripts/06_taxonomy.R
