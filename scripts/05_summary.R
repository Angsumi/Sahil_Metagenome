# Step 5 — Processing summary: reads surviving each step, ASVs per site and shared
# between sites, and rarefaction curves (was sequencing depth sufficient?).
dir.create("work/plots", recursive = TRUE, showWarnings = FALSE)
suppressPackageStartupMessages({ library(data.table); library(ggplot2); library(vegan) })

out <- "results/05_summary"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
raw <- fread("results/01_qc/read_stats.tsv")[read == "R1", .(marker, sample, raw = reads)]
site_of <- c(W1 = "Chandubi (W1)", W2 = "Deepor Beel (W2)")

rows <- list()
for (m in c("18S", "COI")) {
  tr <- fread(file.path("results/03_dada2", m, "track.tsv"))
  cur <- fread(file.path("results/04_curation", sprintf("%s_asv_table_curated.tsv", m)))
  tr[, curated := c(W1 = sum(cur$W1), W2 = sum(cur$W2))[sample]]
  rows[[m]] <- merge(raw[marker == m], tr, by = c("marker", "sample"))
}
track <- rbindlist(rows)[, .(marker, sample, raw, primers_found = input, filtered,
                             merged, nonchim, curated)]
track[, pct_retained := round(100 * curated / raw, 1)]
fwrite(track, file.path(out, "read_tracking.tsv"), sep = "\t")

tl <- melt(track, id.vars = c("marker", "sample"),
           measure.vars = c("raw", "primers_found", "filtered", "merged", "nonchim", "curated"),
           variable.name = "step", value.name = "reads")
tl[, site := site_of[sample]]
tl[, step := factor(step, levels = c("raw", "primers_found", "filtered", "merged", "nonchim", "curated"),
                    labels = c("Raw", "Primers found", "Filtered", "Merged", "Non-chimeric", "Curated"))]
p1 <- ggplot(tl, aes(step, reads, group = site, colour = site)) +
  geom_line(linewidth = 1) + geom_point(size = 2) + facet_wrap(~marker) +
  scale_y_continuous(labels = scales::comma, limits = c(0, NA)) +
  scale_colour_manual(values = c("#2b6c8f", "#c2662d")) +
  labs(x = NULL, y = "Read pairs", colour = NULL, title = "Reads surviving each processing step") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "bottom", axis.text.x = element_text(angle = 30, hjust = 1))
saveRDS(p1, "work/plots/05_read_tracking.rds")
ggsave("docs/img/05_read_tracking.png", p1, width = 9, height = 4.8, dpi = 120)

asv_stats <- list(); curves <- list()
for (m in c("18S", "COI")) {
  cur <- fread(file.path("results/04_curation", sprintf("%s_asv_table_curated.tsv", m)))
  asv_stats[[m]] <- data.table(marker = m,
    W1_asvs = sum(cur$W1 > 0), W2_asvs = sum(cur$W2 > 0),
    shared_asvs = sum(cur$W1 > 0 & cur$W2 > 0), total_asvs = nrow(cur),
    shared_reads_pct_W1 = round(100 * sum(cur$W1[cur$W2 > 0]) / sum(cur$W1), 1),
    shared_reads_pct_W2 = round(100 * sum(cur$W2[cur$W1 > 0]) / sum(cur$W2), 1))
  mat <- t(as.matrix(cur[, .(W1, W2)]))
  asv_stats[[m]][, `:=`(
    bray_curtis = round(as.numeric(vegdist(decostand(mat, "total"), "bray")), 3),
    jaccard = round(as.numeric(vegdist(mat, "jaccard", binary = TRUE)), 3))]
  for (s in rownames(mat)) {
    depth <- unique(round(seq(1, sum(mat[s, ]), length.out = 60)))
    curves[[paste(m, s)]] <- data.table(marker = m, site = site_of[s], depth = depth,
                                        asvs = as.numeric(rarefy(mat[s, ], depth)))
  }
}
asv_stats <- rbindlist(asv_stats)
fwrite(asv_stats, file.path(out, "asv_counts.tsv"), sep = "\t")

p2 <- ggplot(rbindlist(curves), aes(depth, asvs, colour = site)) +
  geom_line(linewidth = 1) + facet_wrap(~marker, scales = "free") +
  scale_x_continuous(labels = scales::comma) +
  scale_colour_manual(values = c("#2b6c8f", "#c2662d")) +
  labs(x = "Reads sampled", y = "ASVs observed", colour = NULL,
       title = "Rarefaction — curves flattening = depth was sufficient") +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom")
saveRDS(p2, "work/plots/05_rarefaction.rds")
ggsave("docs/img/05_rarefaction.png", p2, width = 9, height = 4.5, dpi = 120)

al <- melt(asv_stats, id.vars = "marker",
           measure.vars = c("W1_asvs", "W2_asvs", "shared_asvs"), value.name = "asvs")
al[, variable := factor(variable, labels = c("Chandubi (W1)", "Deepor Beel (W2)", "shared by both"))]
p3 <- ggplot(al, aes(variable, asvs, fill = variable)) +
  geom_col(width = 0.6, show.legend = FALSE) + geom_text(aes(label = asvs), vjust = -0.4) +
  facet_wrap(~marker, scales = "free_y") +
  scale_fill_manual(values = c("#2b6c8f", "#c2662d", "#7a7a7a")) +
  labs(x = NULL, y = "ASVs", title = "ASVs per site after curation") +
  theme_minimal(base_size = 12)
ggsave("docs/img/05_asv_counts.png", p3, width = 8, height = 4.2, dpi = 120)
print(track); print(asv_stats)
