# Step 10 — Summarise the protein-level (DIAMOND blastx) search for COI ASVs with no close DNA match.
# Per ASV: best hit (highest bit score) and the consensus phylum / class shared by >= 70 % of the
# top hits (all hits within 95 % of the best bit score, at least 3 of them); otherwise 'mixed'. Amino-acid identity is read loosely:
# >= 95 % same or closely related genus; 85–95 % same family/order likely; < 85 % phylum/class hint.
suppressPackageStartupMessages({ library(data.table); library(ggplot2) })

out <- "results/10_protein"
b <- fread(file.path(out, "COI_protein_hits.tsv"), header = FALSE, sep = "\t", quote = "",
           col.names = c("asv", "target", "aa_identity", "length", "qcov", "evalue", "bitscore"))
rank_of <- function(x, l) {
  v <- regmatches(x, regexpr(paste0(l, ":[^,]+"), x))
  out <- rep(NA_character_, length(x)); out[grepl(paste0(l, ":"), x)] <- sub("^.:", "", v); out
}
b[, `:=`(phylum = rank_of(target, "p"), class = rank_of(target, "c"), genus = rank_of(target, "g"),
         species = gsub("_", " ", rank_of(target, "s")))]
tax <- fread("results/06_taxonomy/COI_taxonomy.tsv", sep = "\t", quote = "", na.strings = c("", "NA"))
dna <- fread("results/06_taxonomy/COI_blast_unknowns_summary.tsv", sep = "\t", quote = "", na.strings = c("", "NA"))
ids <- readLines("work/protein_ids.txt")

# Hits whose phylum is undefined in the reference (e.g. brown algae: "undef_undef_Eukaryota") are
# labelled by class instead, so they still count against a consensus rather than being ignored.
b[grepl("^undef_", phylum) | is.na(phylum), phylum := fifelse(is.na(class), "unknown", class)]
consensus <- function(x) {
  x <- x[!is.na(x)]
  if (length(x) < 3) return(NA_character_)  # one or two close hits are not a consensus
  t <- sort(table(x), decreasing = TRUE)
  if (t[[1]] / length(x) >= 0.7) names(t)[1] else NA_character_
}
b <- b[order(asv, -bitscore)]
top <- b[, .SD[bitscore >= 0.95 * max(bitscore)], by = asv]
best <- b[, .SD[1], by = asv]
cons <- top[, .(top_hits = .N, consensus_phylum = consensus(phylum), consensus_class = consensus(class)), by = asv]
res <- Reduce(function(x, y) merge(x, y, by = "asv", all.x = TRUE),
              list(data.table(asv = ids),
                   best[, .(asv, best_hit = species, aa_identity, qcov, evalue, best_phylum = phylum, best_class = class)],
                   cons, tax[, .(asv, W1, W2)],
                   dna[, .(asv, dna_identity = ncbi_identity, dna_best_hit = ncbi_best_hit)]))
res[, reading := fcase(is.na(aa_identity), "no protein hit",
                       aa_identity >= 95, "close relative (genus level)",
                       aa_identity >= 85, "same family/order likely",
                       default = "phylum/class hint only")]
res[, `:=`(reads_pct_W1 = round(100 * W1 / sum(tax$W1), 2), reads_pct_W2 = round(100 * W2 / sum(tax$W2), 2))]
setorder(res, -W1)
fwrite(res[, .(asv, reads_pct_W1, reads_pct_W2, dna_identity, dna_best_hit, best_hit, aa_identity, qcov, evalue,
               best_phylum, best_class, consensus_phylum, consensus_class, top_hits, reading)],
       file.path(out, "COI_protein_summary.tsv"), sep = "\t")
fwrite(res[, .(asvs = .N, W1_pct = sum(reads_pct_W1), W2_pct = sum(reads_pct_W2)),
           by = .(consensus_phylum, consensus_class)][order(-(W1_pct + W2_pct))],
       file.path(out, "COI_protein_by_group.tsv"), sep = "\t")

pl <- copy(res[1:min(25, .N)])
pl[, lab := sprintf("%s · %s / %s", asv, fifelse(is.na(consensus_phylum), "mixed", consensus_phylum),
                    fifelse(is.na(consensus_class), "–", consensus_class))]
pl[, lab := factor(lab, levels = rev(lab))]
pl <- melt(pl, id.vars = "lab", measure.vars = c("dna_identity", "aa_identity"),
           variable.name = "level", value.name = "identity")
pl[, level := factor(level, levels = c("dna_identity", "aa_identity"), labels = c("DNA (BLASTn, GenBank)", "Protein (DIAMOND)"))]
p <- ggplot(pl, aes(identity, lab, colour = level, shape = level)) +
  geom_line(aes(group = lab), colour = "#c9c9c9") + geom_point(size = 2.6, stroke = 1) +
  scale_colour_manual(values = c("#c2662d", "#2b6c8f")) +
  scale_shape_manual(values = c(1, 16)) +
  scale_x_continuous(labels = function(x) paste0(x, "%")) +
  labs(x = "Identity to closest known sequence", y = NULL, colour = NULL, shape = NULL,
       title = "Unknown COI sequences: DNA vs protein similarity",
       subtitle = "Label: consensus phylum / class of the closest proteins ('mixed' = no agreement)") +
  theme_minimal(base_size = 11) + theme(legend.position = "bottom", plot.title.position = "plot")
dir.create("work/plots", recursive = TRUE, showWarnings = FALSE)
saveRDS(p, "work/plots/10_protein.rds")
ggsave("docs/img/10_protein.png", p, width = 9.5, height = 7, dpi = 120)
print(res[, .(asv, reads_pct_W1, reads_pct_W2, dna_identity, best_hit, aa_identity, consensus_phylum, consensus_class)])
