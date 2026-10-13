#!/usr/bin/env bash
# Step 2 — Primer removal with Cutadapt.
# Each read must start with its primer (anchored 5'); pairs where either primer is
# missing are discarded. If a read runs through into the opposite primer, that
# (reverse-complemented) primer and everything after it is trimmed too.
#   18S V4 : E572F  CYGCGGTAATTCCAGCTC     / E1009R   AYGGTATCTRWTCRTCTTYG   (Comeau et al. 2011)
#   COI    : mlCOIintF GGWACWGGWTGAACWGTWTAYCCYCC / jgHCO2198 TAIACYTCIGGRTGICCRAARAAYCA (Leray et al. 2013; I -> N)
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=results/02_primer_removal
mkdir -p "$OUT" work/02_trimmed

revcomp() { echo "$1" | rev | tr ACGTRYKMBVDHN TGCAYRMKVBHDN; }

declare -A FWD=( [18S]=CYGCGGTAATTCCAGCTC [COI]=GGWACWGGWTGAACWGTWTAYCCYCC )
declare -A REV=( [18S]=AYGGTATCTRWTCRTCTTYG [COI]=TANACYTCNGGRTGNCCRAARAAYCA )

printf 'marker\tsample\tpairs_in\tpairs_with_both_primers\tpct_kept\n' > "$OUT/cutadapt_summary.tsv"
for m in 18S COI; do
  F=${FWD[$m]}; R=${REV[$m]}
  mkdir -p "work/02_trimmed/$m"
  for r1 in NEW/"$m"/*/*_R1.fastq.gz; do
    s=$(basename "$r1" _R1.fastq.gz); r2=${r1/_R1/_R2}
    cutadapt -j 8 --discard-untrimmed -e 0.15 --minimum-length 50 \
      -g "^${F};required...$(revcomp "$R");optional" -G "^${R};required...$(revcomp "$F");optional" \
      --json "$OUT/${m}_${s}.cutadapt.json" \
      -o "work/02_trimmed/$m/${s}_R1.fastq.gz" -p "work/02_trimmed/$m/${s}_R2.fastq.gz" \
      "$r1" "$r2" > "$OUT/${m}_${s}.cutadapt.log"
    python3 - "$OUT/${m}_${s}.cutadapt.json" "$m" "$s" >> "$OUT/cutadapt_summary.tsv" <<'PY'
import json, sys
j = json.load(open(sys.argv[1]))["read_counts"]
print(f"{sys.argv[2]}\t{sys.argv[3]}\t{j['input']}\t{j['output']}\t{100*j['output']/j['input']:.1f}")
PY
  done
done

# Post-trim length distribution (input to choosing DADA2 truncation lengths)
printf 'marker\tsample\tread\tlength\tcount\n' > "$OUT/trimmed_lengths.tsv"
for f in work/02_trimmed/*/*.fastq.gz; do
  m=$(basename "$(dirname "$f")"); b=$(basename "$f" .fastq.gz)
  zcat "$f" | awk -v m="$m" -v s="${b%_R*}" -v r="${b##*_}" \
    'NR%4==2{c[length($0)]++} END{for(l in c) printf "%s\t%s\t%s\t%d\t%d\n", m, s, r, l, c[l]}' \
    >> "$OUT/trimmed_lengths.tsv"
done
Rscript scripts/02_plot_lengths.R
