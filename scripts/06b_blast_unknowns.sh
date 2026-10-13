#!/usr/bin/env bash
# Step 6b — The COI reference library could not place many abundant ASVs (< 85 % similar
# to anything in it). Send the most abundant of these to NCBI BLAST (core_nt, remote) to
# see what they are (NCBI BLAST URL API, megablast). Top 40 by total reads.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=results/06_taxonomy
N=40

# ASVs whose closest library match is < 85 % (or none), most abundant first
awk -F'\t' 'NR==1 {for (i=1;i<=NF;i++) h[$i]=i; next}
            ($h["identity"]=="" || $h["identity"]<85) {print $h["asv"] "\t" $h["W1"]+$h["W2"]}' \
  "$OUT/COI_taxonomy.tsv" | sort -t$'\t' -k2,2nr | head -n "$N" | cut -f1 > work/blast_ids.txt
awk 'NR==FNR {want[">" $1]=1; next} /^>/ {keep = ($1 in want)} keep' \
  work/blast_ids.txt results/04_curation/COI_asv_seqs_curated.fasta > work/blast_query.fasta

python3 scripts/06b_ncbi_blast.py work/blast_query.fasta "$OUT/COI_blast_unknowns.tsv" 5

# Queries with no megablast hit: retry with sensitive blastn and append
cut -f1 "$OUT/COI_blast_unknowns.tsv" | sort -u > work/blast_hit_ids.txt
grep -vxFf work/blast_hit_ids.txt work/blast_ids.txt > work/blast_nohit_ids.txt || true
if [ -s work/blast_nohit_ids.txt ]; then
  awk 'NR==FNR {want[">" $1]=1; next} /^>/ {keep = ($1 in want)} keep' \
    work/blast_nohit_ids.txt results/04_curation/COI_asv_seqs_curated.fasta > work/blast_query2.fasta
  python3 scripts/06b_ncbi_blast.py work/blast_query2.fasta work/blast_sensitive.tsv 5 --sensitive
  cat work/blast_sensitive.tsv >> "$OUT/COI_blast_unknowns.tsv"
fi

Rscript scripts/06b_blast_summary.R
