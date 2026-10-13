# Step 6 — Turn raw SINTAX + top-hit output into a conservative taxonomy table.
# A rank is accepted only if BOTH
#   (1) SINTAX bootstrap confidence >= 0.80, and
#   (2) the closest reference sequence is similar enough for that rank:
#         COI : species >= 97 %, genus >= 95 %, family >= 90 %, order >= 85 %
#         18S : species >= 99 %, genus >= 97 %, family >= 95 %
# Ranks are accepted top-down; once one fails, all lower ranks are left unassigned.
# PR2 placeholder names (e.g. "Dinophyceae_X", "Enoplea_XX_sp.") are left blank at their
# own rank but do not stop lower ranks (e.g. order "Sphaeropleales_X" -> genus Desmodesmus).
suppressPackageStartupMessages({ library(data.table); library(ggplot2) })

out <- "results/06_taxonomy"
CONF <- 0.80
ranks <- list(
  COI = c(d = "Domain", k = "Kingdom", p = "Phylum", c = "Class", o = "Order",
          f = "Family", g = "Genus", s = "Species"),
  `18S` = c(k = "Domain", d = "Supergroup", p = "Division", c = "Class", o = "Order",
            f = "Family", g = "Genus", s = "Species"))
min_id <- list(COI = c(Order = 85, Family = 90, Genus = 95, Species = 97),
               `18S` = c(Family = 95, Genus = 97, Species = 99))
site_of <- c(W1 = "Chandubi (W1)", W2 = "Deepor Beel (W2)")

parse_sintax <- function(m) {
  s <- fread(file.path(out, sprintf("%s_sintax.tsv", m)), header = FALSE, sep = "\t", quote = "",
             fill = TRUE, col.names = c("asv", "tax", "strand"))[, 1:2]
  r <- ranks[[m]]
  rbindlist(lapply(seq_len(nrow(s)), function(i) {
    parts <- if (is.na(s$tax[i]) || s$tax[i] == "") character() else strsplit(s$tax[i], ",")[[1]]
    d <- data.table(asv = s$asv[i], letter = sub(":.*", "", parts),
                    name = sub("^.:(.*)\\(.*$", "\\1", parts),
                    conf = as.numeric(sub(".*\\((.*)\\)$", "\\1", parts)))
    d[, rank := r[letter]][]
  }), fill = TRUE)
}

summarise_marker <- function(m) {
  r <- unname(ranks[[m]])
  counts <- fread(sprintf("results/04_curation/%s_asv_table_curated.tsv", m))[, .(asv, W1, W2, length)]
  long <- parse_sintax(m)

  hit <- fread(file.path(out, sprintf("%s_tophit.tsv", m)), header = FALSE, sep = "\t", quote = "",
               col.names = c("asv", "target", "identity", "alnlen"))
  hit <- hit[target != "*"][order(asv, -identity)][, .SD[1], by = asv]
  hit[, best_match := gsub("_", " ", sub(".*s:", "", target))]

  # Accept ranks top-down
  long <- merge(long, hit[, .(asv, identity)], by = "asv", all.x = TRUE)
  long[, need := min_id[[m]][rank]][is.na(need), need := 0]
  # PR2 joins division and subdivision ("Chlorophyta-Chlorophyta_X"): keep the division part
  long[, name := sub("-[^-]*_X+$", "", name)]
  long[, placeholder := grepl("(_X+|_sp\\.)$", name) | grepl("^undef_", name)]
  long[, ok := conf >= CONF & !is.na(identity) & identity >= need]
  long[, rank := factor(rank, levels = r)]
  setorder(long, asv, rank)
  long[, ok := cumprod(ok) == 1, by = asv]

  # Placeholders are left blank at their own rank but do not block the ranks below
  wide <- dcast(long[ok == TRUE & !placeholder], asv ~ rank, value.var = "name")
  for (x in r) if (!x %in% names(wide)) wide[, (x) := NA_character_]
  conf_wide <- dcast(long, asv ~ rank, value.var = "conf")
  setnames(conf_wide, setdiff(names(conf_wide), "asv"), paste0("conf_", setdiff(names(conf_wide), "asv")))

  tax <- Reduce(function(a, b) merge(a, b, by = "asv", all.x = TRUE),
                list(counts, wide[, c("asv", r), with = FALSE], conf_wide,
                     hit[, .(asv, identity, best_match)]))
  tax[, deepest := apply(.SD, 1, function(v) { k <- which(!is.na(v)); if (length(k)) r[max(k)] else "Unassigned" }),
      .SDcols = r]
  tax[, label := apply(.SD, 1, function(v) { k <- which(!is.na(v)); if (length(k)) v[max(k)] else "Unassigned" }),
      .SDcols = r]
  tax[, label := gsub("_", " ", label)]
  setorder(tax, -W1)
  fwrite(tax[order(asv)], file.path(out, sprintf("%s_taxonomy.tsv", m)), sep = "\t")
  tax[, marker := m][]
}

tax <- list(COI = summarise_marker("COI"), `18S` = summarise_marker("18S"))

# ---- How deep could reads be named? ----
depth <- rbindlist(lapply(names(tax), function(m) {
  d <- tax[[m]]; r <- unname(ranks[[m]])
  rbindlist(lapply(r[-1], function(x) data.table(
    marker = m, rank = x,
    W1 = round(100 * sum(d$W1[!is.na(d[[x]])]) / sum(d$W1), 1),
    W2 = round(100 * sum(d$W2[!is.na(d[[x]])]) / sum(d$W2), 1))))
}))
fwrite(depth, file.path(out, "assignment_depth.tsv"), sep = "\t")
dl <- melt(depth, id.vars = c("marker", "rank"), variable.name = "sample", value.name = "pct")
dl[, site := site_of[sample]]
dl[, rank := factor(rank, levels = c("Supergroup", "Kingdom", "Division", "Phylum", "Class",
                                     "Order", "Family", "Genus", "Species"))]
p1 <- ggplot(dl, aes(rank, pct, colour = site, group = site)) +
  geom_line(linewidth = 1) + geom_point(size = 2.2) + facet_wrap(~marker, scales = "free_x") +
  scale_y_continuous(limits = c(0, 100), labels = function(x) paste0(x, "%")) +
  scale_colour_manual(values = c("#2b6c8f", "#c2662d")) +
  labs(x = NULL, y = "Reads named at this rank", colour = NULL,
       title = "How far down the tree of life could reads be named?") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "bottom", axis.text.x = element_text(angle = 30, hjust = 1))
ggsave("docs/img/06_assignment_depth.png", p1, width = 9, height = 4.8, dpi = 120)

# ---- Composition per lake ----
comp_plot <- function(m, rank, top, file, title) {
  d <- copy(tax[[m]])
  d[, grp := fifelse(is.na(get(rank)), "Unassigned", gsub("_", " ", get(rank)))]
  cmp <- d[, .(W1 = sum(W1), W2 = sum(W2)), by = grp]
  cmp[, `:=`(W1 = 100 * W1 / sum(W1), W2 = 100 * W2 / sum(W2))]
  keep <- cmp[grp != "Unassigned"][order(-(W1 + W2))][seq_len(min(top, .N)), grp]
  cmp[!grp %in% c(keep, "Unassigned"), grp := "Other named"]
  cmp <- cmp[, .(W1 = sum(W1), W2 = sum(W2)), by = grp]
  fwrite(cmp[order(-(W1 + W2))][, `:=`(W1 = round(W1, 2), W2 = round(W2, 2))],
         file.path(out, sprintf("%s_composition_%s.tsv", m, tolower(rank))), sep = "\t")
  cl <- melt(cmp, id.vars = "grp", variable.name = "sample", value.name = "pct")
  cl[, site := site_of[sample]]
  lv <- c(keep, "Other named", "Unassigned")
  cl[, grp := factor(grp, levels = rev(lv[lv %in% grp]))]
  pal <- c("#2b6c8f", "#c2662d", "#5a9e6f", "#8a6bb0", "#d4a72c", "#4fa3b8", "#b5536b",
           "#7d8c3a", "#a0785a", "#5d6fb3", "#c98bb9", "#3f7f6e")
  cols <- setNames(c(pal[seq_along(keep)], "#c9c9c9", "#ededed"), c(keep, "Other named", "Unassigned"))
  p <- ggplot(cl, aes(site, pct, fill = grp)) +
    geom_col(width = 0.55, colour = "white", linewidth = 0.3) +
    scale_fill_manual(values = cols, breaks = lv) +
    scale_y_continuous(labels = function(x) paste0(x, "%"), expand = c(0, 0)) +
    labs(x = NULL, y = "Share of reads", fill = rank, title = title) +
    theme_minimal(base_size = 12) + guides(fill = guide_legend(ncol = 1))
  ggsave(file, p, width = 7.5, height = 5.2, dpi = 120)
}
comp_plot("COI", "Phylum", 8, "docs/img/06_COI_phylum.png", "COI — animal groups (phylum)")
comp_plot("COI", "Class", 10, "docs/img/06_COI_class.png", "COI — class")
comp_plot("18S", "Division", 11, "docs/img/06_18S_division.png", "18S — major groups (division)")
comp_plot("18S", "Class", 12, "docs/img/06_18S_class.png", "18S — class")

# ---- Named genera and species ----
named <- rbindlist(lapply(names(tax), function(m) {
  d <- tax[[m]][!is.na(Genus)]
  grp_col <- if (m == "COI") "Phylum" else "Division"
  d[, .(marker = m, group = get(grp_col)[1], Genus,
        Species = gsub("_", " ", Species),
        asvs = .N, W1_reads = sum(W1), W2_reads = sum(W2),
        W1_pct = round(100 * sum(W1) / sum(tax[[m]]$W1), 2),
        W2_pct = round(100 * sum(W2) / sum(tax[[m]]$W2), 2),
        best_identity = max(identity)), by = .(Genus, Species)][, -(1:2)]
}))
setorder(named, marker, -W1_pct)
fwrite(named, file.path(out, "named_genera_species.tsv"), sep = "\t")

# ---- Identity of best match, weighted by reads ----
idd <- rbindlist(lapply(names(tax), function(m) tax[[m]][, .(marker = m, identity, reads = W1 + W2)]))
idd[is.na(identity), identity := 69]
p3 <- ggplot(idd, aes(identity, weight = reads)) +
  geom_histogram(binwidth = 1, fill = "#2b6c8f") + facet_wrap(~marker, scales = "free_y") +
  geom_vline(data = data.table(marker = c("COI", "18S"), x = c(97, 99)), aes(xintercept = x),
             linetype = 2, colour = "#c2662d") +
  scale_y_continuous(labels = scales::comma) +
  labs(x = "Similarity to closest reference sequence (%)", y = "Reads",
       title = "How close is each sequence to something already in the library?",
       subtitle = "Dashed line: similarity needed to accept a species name") +
  theme_minimal(base_size = 12)
ggsave("docs/img/06_identity.png", p3, width = 9, height = 4.5, dpi = 120)

# ---- Summary ----
summ <- rbindlist(lapply(names(tax), function(m) {
  d <- tax[[m]]
  data.table(marker = m, asvs = nrow(d),
             asvs_to_genus = sum(!is.na(d$Genus)), asvs_to_species = sum(!is.na(d$Species)),
             named_genera = uniqueN(na.omit(d$Genus)), named_species = uniqueN(na.omit(d$Species)),
             reads_below_85pct_identity = round(100 * sum((d$W1 + d$W2)[is.na(d$identity) | d$identity < 85]) /
                                                  sum(d$W1 + d$W2), 1))
}))
fwrite(summ, file.path(out, "taxonomy_summary.tsv"), sep = "\t")
print(summ); print(depth)
print(named[, .(marker, group, Genus, Species, W1_pct, W2_pct, best_identity)][order(marker, -(W1_pct + W2_pct))][, head(.SD, 15), by = marker])
