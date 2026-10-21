# Step 12 — Manuscript package (re-run after step 15 to include the microscopy comparison): multi-panel figures (300 dpi PNG + vector PDF), main tables
# (CSV) and one supplementary workbook (XLSX). Reads only the outputs of steps 1–11.
suppressPackageStartupMessages({ library(data.table); library(ggplot2); library(patchwork); library(openxlsx) })

out <- "results/12_manuscript"
dir.create(file.path(out, "figures"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(out, "tables"), recursive = TRUE, showWarnings = FALSE)
rd <- function(p) fread(p, sep = "\t", quote = "", na.strings = c("", "NA"))
pl <- function(n) readRDS(file.path("work/plots", paste0(n, ".rds")))
pub <- theme(plot.title = element_blank(), plot.subtitle = element_blank(),
             text = element_text(size = 10), legend.text = element_text(size = 9))
save_fig <- function(p, name, w, h) {
  ggsave(file.path(out, "figures", paste0(name, ".png")), p, width = w, height = h, dpi = 300, bg = "white")
  ggsave(file.path(out, "figures", paste0(name, ".pdf")), p, width = w, height = h, device = cairo_pdf)
}

# ---- Figures ----
f1 <- (pl("05_read_tracking") + pub) / (pl("05_rarefaction") + pub) + plot_annotation(tag_levels = "A")
save_fig(f1, "Figure1_read_processing_rarefaction", 7.5, 8)
f2 <- (pl("09_18S_roles") + pub) / (pl("09_COI_groups") + pub) + plot_annotation(tag_levels = "A")
save_fig(f2, "Figure2_community_composition", 8.5, 7.5)
f3 <- (pl("08_alpha") + pub) / (pl("08_overlap") + pub) + plot_layout(heights = c(1, 1.2)) +
  plot_annotation(tag_levels = "A")
save_fig(f3, "Figure3_diversity_overlap", 8, 9)
save_fig(pl("09_genera_heatmap") + pub, "Figure4_top_genera_heatmap", 7.5, 8.5)
save_fig(pl("10_protein") + pub, "Figure5_unknowns_DNA_vs_protein", 8, 7)
save_fig(pl("11_rotifer_genera") + pub, "Figure6_rotifer_genera", 7.5, 4.5)
save_fig(pl("15_microscopy") + pub, "Figure7_microscopy_vs_DNA", 8, 3.8)

# ---- Table 1: sequencing and processing summary ----
tr <- rd("results/05_summary/read_tracking.tsv")
asv <- rbindlist(lapply(c("18S", "COI"), function(m) {
  d <- rd(sprintf("results/04_curation/%s_asv_table_curated.tsv", m))
  data.table(marker = m, sample = c("W1", "W2"), ASVs = c(sum(d$W1 > 0), sum(d$W2 > 0)))
}))
t1 <- merge(tr, asv, by = c("marker", "sample"))
t1[, site := fifelse(sample == "W1", "Chandubi Beel", "Deepor Beel")]
t1 <- t1[, .(Marker = marker, Site = site, `Raw read pairs` = raw, `Primers found` = primers_found,
             `Quality-filtered` = filtered, Merged = merged, `Non-chimeric` = nonchim,
             `Curated` = curated, `% retained` = pct_retained, ASVs)]
fwrite(t1, file.path(out, "tables", "Table1_sequencing_summary.csv"))

# ---- Table 2: diversity ----
al <- rd("results/08_diversity/alpha_diversity.tsv")
t2 <- al[, .(Marker = marker, Site = fifelse(sample == "W1", "Chandubi Beel", "Deepor Beel"),
             `Rarefied depth` = rarefied_to, `Observed ASVs` = round(observed),
             Shannon = round(shannon, 2), `Simpson (1-D)` = round(simpson, 3),
             `Pielou J'` = round(pielou, 2), `Hill q1` = round(hill_q1, 1), `Hill q2` = round(hill_q2, 1))]
ov <- rd("results/08_diversity/overlap_by_level.tsv")
fwrite(t2, file.path(out, "tables", "Table2_alpha_diversity.csv"))
fwrite(ov, file.path(out, "tables", "Table3_overlap_between_lakes.csv"))

# ---- Table 4: named taxa ----
nm <- rd("results/06_taxonomy/named_genera_species.tsv")
t4 <- nm[, .(Marker = marker, Group = group, Genus, Species = fifelse(is.na(Species), "", Species),
             ASVs = asvs, `Chandubi (% reads)` = W1_pct, `Deepor (% reads)` = W2_pct,
             `Best identity (%)` = best_identity)][order(Marker, Group, Genus)]
fwrite(t4, file.path(out, "tables", "Table4_named_taxa.csv"))
fwrite(rd("results/09_ecology/indicator_taxa.tsv"), file.path(out, "tables", "Table5_indicator_taxa.csv"))

# ---- Supplementary workbook ----
seqs <- function(m) {
  x <- rd(sprintf("results/04_curation/%s_asv_table_curated.tsv", m))[, .(asv, sequence)]
  merge(rd(sprintf("results/06_taxonomy/%s_taxonomy.tsv", m)), x, by = "asv")
}
sheets <- list(
  S1_18S_ASVs = seqs("18S"),
  S2_COI_ASVs = merge(seqs("COI"), rd("results/09_ecology/COI_asv_groups.tsv")[, .(asv, group)], by = "asv"),
  S3_read_tracking = tr,
  S4_COI_BLASTn_unknowns = rd("results/06_taxonomy/COI_blast_unknowns_summary.tsv"),
  S5_18S_ecological_roles = rd("results/09_ecology/18S_ecological_roles.tsv"),
  S6_COI_animal_groups = rd("results/09_ecology/COI_animal_groups.tsv"),
  S7_animal_genera_by_marker = rd("results/09_ecology/animal_genera_by_marker.tsv"),
  S8_rotifer_MOTUs = rd("results/11_rotifer_index/COI_motus.tsv"),
  S9_QBT_index = rd("results/11_rotifer_index/QBT_index.tsv"))
sheets$S10_COI_protein_search <- rd("results/10_protein/COI_protein_summary.tsv")
sheets$S11_Deepor_rotifers_vs_micro <- rd("results/15_microscopy/rotifers_microscopy_vs_DNA.tsv")
sheets$S12_Deepor_algae_vs_micro <- rd("results/15_microscopy/algae_genera_microscopy_vs_DNA.tsv")
wb <- createWorkbook()
for (n in names(sheets)) {
  addWorksheet(wb, n)
  writeData(wb, n, sheets[[n]], headerStyle = createStyle(textDecoration = "bold"))
  freezePane(wb, n, firstRow = TRUE)
  setColWidths(wb, n, cols = seq_len(ncol(sheets[[n]])), widths = "auto")
}
saveWorkbook(wb, file.path(out, "tables", "Supplementary_Tables_S1-S12.xlsx"), overwrite = TRUE)

# ASV sequences for deposition alongside the paper
for (m in c("18S", "COI"))
  file.copy(sprintf("results/04_curation/%s_asv_seqs_curated.fasta", m),
            file.path(out, "tables", sprintf("Supplementary_%s_ASVs.fasta", m)), overwrite = TRUE)
print(list.files(out, recursive = TRUE))
