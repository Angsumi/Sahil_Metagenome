# Step 11 — Rotifer genera and the Brachionus:Trichocerca quotient (QB/T) per lake.
# Genus of each 97 % MOTU: the reference-library genus of any member ASV; otherwise the genus
# of the best NCBI BLAST hit when identity >= 80 % ("provisional" — a related genus is possible).
# QB/T interpretation (Sládeček 1983): < 1 oligotrophic, 1–2 mesotrophic, > 2 eutrophic.
dir.create("work/plots", recursive = TRUE, showWarnings = FALSE)
suppressPackageStartupMessages({ library(data.table); library(ggplot2) })

out <- "results/11_rotifer_index"
uc <- fread(file.path(out, "COI_motu97.uc"), header = FALSE, sep = "\t")
uc <- uc[V1 %in% c("S", "H"), .(asv = sub(";size=.*", "", V9),
                                centroid = sub(";size=.*", "", fifelse(V1 == "S", V9, V10)))]
grp <- fread("results/09_ecology/COI_asv_groups.tsv", sep = "\t", quote = "", na.strings = c("", "NA"))
bl <- fread("results/06_taxonomy/COI_blast_unknowns_summary.tsv", sep = "\t", quote = "", na.strings = c("", "NA"))
bl[, blast_genus := fifelse(ncbi_identity >= 80 & !grepl("environmental|sample", ncbi_best_hit),
                            sub(" .*", "", ncbi_best_hit), NA_character_)]

d <- merge(uc, grp, by = "asv")
d <- merge(d, bl[, .(asv, blast_genus)], by = "asv", all.x = TRUE)
motu <- d[, .(W1 = sum(W1), W2 = sum(W2), asvs = .N,
              rotifer = any(group == "Rotifers"),
              genus = na.omit(c(Genus, blast_genus))[1],
              genus_source = fcase(any(!is.na(Genus)), "reference library",
                                   any(!is.na(blast_genus)), "BLAST (provisional)",
                                   default = NA_character_)), by = centroid]
fwrite(motu[order(-(W1 + W2))], file.path(out, "COI_motus.tsv"), sep = "\t")

rot <- motu[rotifer == TRUE]
by_genus <- rbindlist(lapply(c("W1", "W2"), function(s) {
  x <- rot[get(s) > 0]
  x[, .(motus = .N, reads = sum(get(s)), source = paste(sort(unique(na.omit(genus_source))), collapse = "; ")),
    by = .(genus = fifelse(is.na(genus), "unassigned rotifer", genus))][, sample := s][]
}))
setcolorder(by_genus, c("sample", "genus"))
fwrite(by_genus[order(sample, -motus)], file.path(out, "rotifer_genera_by_lake.tsv"), sep = "\t")

qbt <- rbindlist(lapply(c("W1", "W2"), function(s) {
  x <- rot[get(s) > 0]
  b <- sum(x$genus %in% "Brachionus"); t <- sum(x$genus %in% "Trichocerca")
  data.table(sample = s, rotifer_motus = nrow(x), brachionus_motus = b, trichocerca_motus = t,
             QBT = if (t > 0) round(b / t, 2) else NA_real_,
             reading = if (t == 0) "undefined (no Trichocerca)" else
               fcase(b / t < 1, "oligotrophic", b / t <= 2, "mesotrophic", default = "eutrophic"))
}))
fwrite(qbt, file.path(out, "QBT_index.tsv"), sep = "\t")

site_of <- c(W1 = "Chandubi (W1)", W2 = "Deepor Beel (W2)")
pg <- by_genus[genus != "unassigned rotifer"]
pg[, site := site_of[sample]]
pg[, genus := factor(genus, levels = pg[, sum(motus), by = genus][order(V1), genus])]
p <- ggplot(pg, aes(motus, genus, fill = site)) +
  geom_col(position = position_dodge(width = 0.75), width = 0.7) +
  geom_text(aes(label = motus), position = position_dodge(width = 0.75), hjust = -0.3, size = 3.3) +
  scale_fill_manual(values = c("#2b6c8f", "#c2662d")) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(x = "Species-level clusters (97 % MOTUs)", y = NULL, fill = NULL,
       title = "Rotifer genera in each lake (COI)",
       subtitle = sprintf("QB/T — Chandubi: %s · Deepor: %s  (<1 oligotrophic, 1–2 mesotrophic, >2 eutrophic)",
                          qbt[sample == "W1", QBT], qbt[sample == "W2", QBT])) +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom", plot.title.position = "plot")
saveRDS(p, "work/plots/11_rotifer_genera.rds")
ggsave("docs/img/11_rotifer_genera.png", p, width = 9, height = 5, dpi = 120)
print(qbt); print(by_genus[order(sample, -motus)])
