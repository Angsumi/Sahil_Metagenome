# Step 8 — Diversity.
#  (a) Alpha diversity per lake, after rarefying both lakes to the same depth
#      (mean of 100 random subsamples): observed ASVs, Shannon, Simpson, Pielou's evenness,
#      and Hill numbers (q0 = richness, q1 = exp(Shannon), q2 = inverse Simpson) —
#      the "effective number" of equally common types.
#  (b) Overlap between lakes at ASV, genus and species level (shared / unique, Jaccard,
#      Bray–Curtis). One sample per lake: descriptive only, no significance tests.
# Chao1 is not reported: DADA2 discards singletons, which Chao1 depends on.
suppressPackageStartupMessages({ library(data.table); library(ggplot2); library(vegan) })

out <- "results/08_diversity"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
site_of <- c(W1 = "Chandubi (W1)", W2 = "Deepor Beel (W2)")
set.seed(2026)

tax <- list(`18S` = fread("results/06_taxonomy/18S_taxonomy.tsv", sep = "\t", quote = "", na.strings = c("", "NA")),
            COI = fread("results/06_taxonomy/COI_taxonomy.tsv", sep = "\t", quote = "", na.strings = c("", "NA")))

# ---- (a) alpha diversity ----
alpha <- rbindlist(lapply(names(tax), function(m) {
  mat <- t(as.matrix(tax[[m]][, .(W1, W2)]))
  depth <- min(rowSums(mat))
  reps <- replicate(100, {
    r <- rrarefy(mat, depth)
    H <- diversity(r, "shannon"); S <- specnumber(r)
    cbind(observed = S, shannon = H, simpson = diversity(r, "simpson"),
          pielou = H / log(S), hill_q1 = exp(H), hill_q2 = diversity(r, "invsimpson"))
  }, simplify = "array")
  mean_mat <- apply(reps, c(1, 2), mean)
  data.table(marker = m, sample = rownames(mat), rarefied_to = depth, round(mean_mat, 3))
}))
fwrite(alpha, file.path(out, "alpha_diversity.tsv"), sep = "\t")

hl <- melt(alpha, id.vars = c("marker", "sample"), measure.vars = c("observed", "hill_q1", "hill_q2"),
           variable.name = "q", value.name = "value")
hl[, q := factor(q, levels = c("observed", "hill_q1", "hill_q2"),
                 labels = c("All types\n(richness)", "Typical types\n(exp Shannon)", "Dominant types\n(inv. Simpson)"))]
hl[, site := site_of[sample]]
p1 <- ggplot(hl, aes(q, value, fill = site)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.65) +
  geom_text(aes(label = round(value)), position = position_dodge(width = 0.7), vjust = -0.4, size = 3.4) +
  facet_wrap(~marker, scales = "free_y") +
  scale_fill_manual(values = c("#2b6c8f", "#c2662d")) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(x = NULL, y = "Effective number of ASVs", fill = NULL,
       title = "How diverse is each lake?",
       subtitle = "Both lakes subsampled to equal depth. Left to right: counting every type → only the common ones.") +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom", plot.title.position = "plot")
ggsave("docs/img/08_alpha.png", p1, width = 9.5, height = 5, dpi = 120)

# ---- (b) overlap at several levels ----
overlap <- rbindlist(lapply(names(tax), function(m) {
  d <- tax[[m]]
  rbindlist(lapply(c("ASV", "Genus", "Species"), function(level) {
    key <- if (level == "ASV") d$asv else d[[level]]
    agg <- d[!is.na(key), .(W1 = sum(W1), W2 = sum(W2)), by = .(k = key[!is.na(key)])]
    if (nrow(agg) == 0) return(NULL)
    mat <- t(as.matrix(agg[, .(W1, W2)]))
    data.table(marker = m, level = level,
               chandubi_only = sum(agg$W1 > 0 & agg$W2 == 0), deepor_only = sum(agg$W1 == 0 & agg$W2 > 0),
               shared = sum(agg$W1 > 0 & agg$W2 > 0), total = nrow(agg),
               pct_shared = round(100 * sum(agg$W1 > 0 & agg$W2 > 0) / nrow(agg), 1),
               jaccard_similarity = round(1 - as.numeric(vegdist(mat, "jaccard", binary = TRUE)), 3),
               bray_curtis_dissimilarity = round(as.numeric(vegdist(decostand(mat, "total"), "bray")), 3))
  }))
}))
fwrite(overlap, file.path(out, "overlap_by_level.tsv"), sep = "\t")

ol <- melt(overlap, id.vars = c("marker", "level"), measure.vars = c("chandubi_only", "shared", "deepor_only"),
           variable.name = "where", value.name = "n")
ol[, where := factor(where, levels = c("chandubi_only", "shared", "deepor_only"),
                     labels = c("Chandubi only", "Both lakes", "Deepor only"))]
ol[, pct := 100 * n / sum(n), by = .(marker, level)]
ol[, level := factor(level, levels = c("ASV", "Genus", "Species"))]
p2 <- ggplot(ol, aes(pct, level, fill = where)) +
  geom_col(width = 0.6, position = position_stack(reverse = TRUE)) +
  geom_text(aes(label = ifelse(n > 0, n, "")), position = position_stack(vjust = 0.5, reverse = TRUE),
            colour = "white", size = 3.4) +
  facet_wrap(~marker, ncol = 1) +
  scale_fill_manual(values = c("#2b6c8f", "#8c8c8c", "#c2662d")) +
  scale_x_continuous(labels = function(x) paste0(x, "%"), expand = expansion(mult = c(0, 0.02))) +
  labs(x = "Share of types (numbers = count)", y = NULL, fill = NULL,
       title = "What do the two lakes have in common?") +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom", plot.title.position = "plot")
ggsave("docs/img/08_overlap.png", p2, width = 9, height = 5.5, dpi = 120)
print(alpha); print(overlap)
