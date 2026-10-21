#!/usr/bin/env bash
# Step 10 — Protein-level identification of COI ASVs that have no close DNA match in GenBank
# (best BLASTn identity < 90 %). DNA changes faster than the protein it encodes, so comparing
# translated sequences can still place a sequence in its phylum or class when DNA similarity
# is too low to say anything.
# Reference: the Eukaryote CO1 Reference Set (step 6) translated to protein — each sequence in
# the reading frame with fewest stop codons, invertebrate mitochondrial code (table 5).
# Search: DIAMOND blastx (local; NCBI's online BLASTx queue proved unusable for this run).
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=results/10_protein
REFS=work/refs
mkdir -p "$OUT"

if [ ! -s "$REFS/COIv5.1.0_protein.dmnd" ]; then
  seqkit translate -j 8 -T 5 -f 1,2,3 -w 0 "$REFS/COIv5.1.0_sintax.fasta" 2>/dev/null |
    awk '/^>/ { h = $1; sub(/_frame=[0-9]+$/, "", h); next }
         { n = gsub(/\*/, "X"); if (!(h in best) || n < best[h]) { best[h] = n; seq[h] = $0 } }
         END { for (k in seq) print k "\n" seq[k] }' > "$REFS/COIv5.1.0_protein.faa"
  diamond makedb --in "$REFS/COIv5.1.0_protein.faa" -d "$REFS/COIv5.1.0_protein" --quiet
  rm "$REFS/COIv5.1.0_protein.faa"
fi

# Query: all COI ASVs that were looked up in GenBank and had no >= 90 % DNA match
awk -F'\t' 'NR==1 {for (i=1;i<=NF;i++) h[$i]=i; next}
            ($h["ncbi_identity"]=="" || $h["ncbi_identity"]<90) {print $h["asv"]}' \
  results/06_taxonomy/COI_blast_unknowns_summary.tsv > work/protein_ids.txt
awk 'NR==FNR {want[">" $1]=1; next} /^>/ {keep = ($1 in want)} keep' \
  work/protein_ids.txt results/04_curation/COI_asv_seqs_curated.fasta > work/protein_query.fasta

diamond blastx -q work/protein_query.fasta -d "$REFS/COIv5.1.0_protein" --query-gencode 5 \
  --ultra-sensitive --max-target-seqs 25 --evalue 1e-10 --threads 16 --quiet \
  --outfmt 6 qseqid sseqid pident length qcovhsp evalue bitscore -o "$OUT/COI_protein_hits.tsv"

Rscript scripts/10_protein_summary.R
