# Step 4 — ASV curation.
#  COI : a real COI ASV is protein-coding. Keep ASVs whose length differs from the 313 bp
#        Leray fragment by whole codons (±10 codons) AND translate with no stop codon
#        under the invertebrate mitochondrial code (NCBI table 5). Others are likely
#        NUMTs / pseudogenes or artefacts.
#  18S : keep ASVs within the expected V4 (E572F–E1009R) length window, 350–480 bp.
suppressPackageStartupMessages({ library(Biostrings); library(data.table); library(ggplot2) })

out <- "results/04_curation"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
read_asv <- function(m) fread(file.path("results/03_dada2", m, "asv_table.tsv"))

# ---- COI ----
coi <- read_asv("COI")
dna <- DNAStringSet(coi$sequence)
code5 <- getGeneticCode("5")
stops_in_frame <- sapply(1:3, function(f)
  vcountPattern("*", suppressWarnings(translate(subseq(dna, f), genetic.code = code5,
                                                if.fuzzy.codon = "X"))))
# The coding frame is the one that is stop-free for the most reads
frame <- which.max(colSums((stops_in_frame == 0) * (coi$W1 + coi$W2)))
coi[, `:=`(stops = stops_in_frame[, frame],
           codon_ok = abs(length - 313) %% 3 == 0 & abs(length - 313) <= 30)]
coi[, keep := codon_ok & stops == 0]
coi[, reason := fifelse(keep, "kept", fifelse(!codon_ok, "length not codon-compatible", "stop codon in frame"))]

# ---- 18S ----
s18 <- read_asv("18S")
s18[, keep := length >= 350 & length <= 480]
s18[, reason := fifelse(keep, "kept", "outside 350–480 bp")]

# ---- Write curated tables + summary ----
summ <- rbindlist(lapply(list(COI = coi, `18S` = s18), function(d)
  d[, .(asvs = .N, W1_reads = sum(W1), W2_reads = sum(W2)), by = reason]), idcol = "marker")
fwrite(summ, file.path(out, "curation_summary.tsv"), sep = "\t")
fwrite(coi[, .(asv, length, stops, reason)], file.path(out, "COI_frame_check.tsv"), sep = "\t")
cat(sprintf("COI coding frame: +%d\n", frame), file = file.path(out, "COI_frame.txt"))

for (m in c("COI", "18S")) {
  d <- if (m == "COI") coi else s18
  k <- d[keep == TRUE]
  fwrite(k[, .(asv, W1, W2, length, sequence)], file.path(out, sprintf("%s_asv_table_curated.tsv", m)), sep = "\t")
  writeLines(paste0(">", k$asv, "\n", k$sequence), file.path(out, sprintf("%s_asv_seqs_curated.fasta", m)))
}

# ---- Plot: ASV length vs reads, coloured by curation outcome ----
both <- rbind(coi[, .(marker = "COI", length, reads = W1 + W2, reason)],
              s18[, .(marker = "18S", length, reads = W1 + W2, reason)])
p <- ggplot(both, aes(length, reads, colour = reason)) +
  geom_point(alpha = 0.7, size = 1.8) + facet_wrap(~marker, scales = "free_x") +
  scale_y_log10(labels = scales::comma) +
  scale_colour_manual(values = c(kept = "#2b6c8f", `stop codon in frame` = "#d95f02",
                                 `length not codon-compatible` = "#e7a33e",
                                 `outside 350–480 bp` = "#e7a33e")) +
  labs(x = "ASV length (bp)", y = "Reads (log scale)", colour = NULL,
       title = "ASV curation — each point is one ASV") +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom")
ggsave("docs/img/04_curation.png", p, width = 9, height = 4.8, dpi = 120)
print(summ)
