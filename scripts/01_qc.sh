#!/usr/bin/env bash
# Step 1 — Raw read QC: checksum verification, FastQC + MultiQC, per-file read stats,
# and DADA2 quality profiles. Inputs: NEW/<marker>/<site>/*.fastq.gz
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=results/01_qc
mkdir -p "$OUT" work/01_fastqc docs/img

# 1a. MD5 verification against the vendor checksum files
: > "$OUT/md5_check.tsv"
for m in 18S COI; do
  while read -r hash file; do
    path=$(ls NEW/"$m"/*/"$file")
    got=$(md5sum < "$path" | cut -d' ' -f1)
    status=$([ "$got" = "$hash" ] && echo OK || echo FAIL)
    printf '%s\t%s\t%s\n' "$m" "$path" "$status" >> "$OUT/md5_check.tsv"
  done < NEW/"$m"/MD5SUM_Raw.txt
done

# 1b. FastQC on every raw file, summarised with MultiQC
find NEW -name '*.fastq.gz' -print0 | xargs -0 fastqc -q -t 8 --outdir work/01_fastqc
multiqc -q -f -o "$OUT/multiqc" -n multiqc_raw.html work/01_fastqc

# 1c. Read count / length / GC / mean quality per file
printf 'marker\tsite\tsample\tread\treads\tmean_len\tgc_pct\tmean_q\n' > "$OUT/read_stats.tsv"
for f in NEW/*/*/*.fastq.gz; do
  marker=$(echo "$f" | cut -d/ -f2); site=$(echo "$f" | cut -d/ -f3)
  base=$(basename "$f" .fastq.gz); sample=${base%_R*}; read=${base##*_}
  zcat "$f" | awk -v m="$marker" -v s="$site" -v sm="$sample" -v r="$read" '
    BEGIN { for (i = 33; i < 127; i++) ord[sprintf("%c", i)] = i - 33 }
    NR % 4 == 2 { n++; len += length($0); gc += gsub(/[GCgc]/, "") }
    NR % 4 == 0 { for (i = 1; i <= length($0); i++) q += ord[substr($0, i, 1)]; qn += length($0) }
    END { printf "%s\t%s\t%s\t%s\t%d\t%.1f\t%.1f\t%.1f\n", m, s, sm, r, n, len/n, 100*gc/len, q/qn }' \
    >> "$OUT/read_stats.tsv"
done

# 1d. Per-position quality profiles (DADA2)
Rscript scripts/01_quality_profiles.R
