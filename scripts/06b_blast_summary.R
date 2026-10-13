# Step 6b — Summarise NCBI BLAST results for the most abundant COI ASVs that the
# COI reference library could not place. Best hit = highest % identity × query cover.
# Interpretation: >= 97 % species-level match, >= 90 % same genus/family likely,
# 80-90 % only a distant relative is on record (phylum-level hint only);
# < 80 % nothing informative is on record.
suppressPackageStartupMessages({ library(data.table); library(ggplot2) })

out <- "results/06_taxonomy"
b <- fread(file.path(out, "COI_blast_unknowns.tsv"), header = FALSE, sep = "\t", quote = "",
           col.names = c("asv", "acc", "pident", "length", "qcovs", "evalue", "taxid", "name",
                         "kingdom", "phylum", "class"))
b[, group := fifelse(phylum != "", phylum, fifelse(kingdom != "", kingdom, "unknown"))]
tax <- fread(file.path(out, "COI_taxonomy.tsv"), sep = "\t", quote = "")
ids <- readLines("work/blast_ids.txt")

best <- b[order(asv, -(pident * qcovs))][, .SD[1], by = asv]
res <- merge(data.table(asv = ids), best, by = "asv", all.x = TRUE)
res <- merge(res, tax[, .(asv, W1, W2, library_identity = identity, library_label = label)], by = "asv")
res[, match := fcase(is.na(pident), "no hit in NCBI",
                     pident >= 97 & qcovs >= 90, "species-level match",
                     pident >= 90 & qcovs >= 80, "close relative (genus/family)",
                     default = "distant relative only")]
res[is.na(group), group := "no hit"]
# Below 80 % identity the best hit is not informative even about the phylum
res[!is.na(pident) & pident < 80, group := "no relative >= 80 %"]
setorder(res, -W1)
res[, reads_pct_W1 := round(100 * W1 / sum(tax$W1), 2)][, reads_pct_W2 := round(100 * W2 / sum(tax$W2), 2)]
fwrite(res[, .(asv, W1, W2, reads_pct_W1, reads_pct_W2, library_identity, ncbi_best_hit = name,
               ncbi_phylum = group, ncbi_class = class, ncbi_identity = pident, ncbi_query_cover = qcovs, accession = acc, match)],
       file.path(out, "COI_blast_unknowns_summary.tsv"), sep = "\t")

# Reads in these ASVs, by NCBI group and match quality
agg <- res[, .(W1 = sum(W1), W2 = sum(W2)), by = .(group, match)]
fwrite(agg[order(-(W1 + W2))], file.path(out, "COI_blast_unknowns_by_group.tsv"), sep = "\t")

res[, lab := sprintf("%s  ·  %s (%s%%)", asv,
                     fcase(is.na(name), "no hit", pident < 80, "no relative on record", default = name),
                     ifelse(is.na(pident), "–", format(round(pident, 1))))]
res[, lab := factor(lab, levels = rev(lab))]
pl <- melt(res[1:min(25, .N)], id.vars = c("lab", "match"), measure.vars = c("W1", "W2"),
           variable.name = "sample", value.name = "reads")
pl[, site := c(W1 = "Chandubi (W1)", W2 = "Deepor Beel (W2)")[sample]]
p <- ggplot(pl, aes(reads, lab, fill = site)) +
  geom_col(position = position_dodge(width = 0.75), width = 0.7) +
  scale_fill_manual(values = c("#2b6c8f", "#c2662d")) +
  scale_x_continuous(labels = scales::comma) +
  labs(x = "Reads", y = NULL, fill = NULL,
       title = "25 most abundant 'unknown' COI sequences: closest match in NCBI",
       subtitle = "Label: best NCBI hit (% identical). Below ~90 % only a distant relative is on record.") +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom", plot.title.position = "plot")
ggsave("docs/img/06b_blast_unknowns.png", p, width = 10, height = 8, dpi = 120)
print(res[, .(asv, W1, W2, library_identity, name, group, pident, qcovs, match)])
print(agg[order(-(W1 + W2))])
