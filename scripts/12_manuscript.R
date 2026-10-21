# Step 12 — Manuscript package (re-run after step 15 to include the microscopy comparison): multi-panel figures (300 dpi PNG + vector PDF), main tables
# (CSV) and one supplementary workbook (XLSX). Reads only the outputs of steps 1–11.
suppressPackageStartupMessages({ library(data.table); library(ggplot2); library(patchwork); library(openxlsx) })

out <- "results/12_manuscript"
dir.create(file.path(out, "figures"), recursive = TRUE, showWarnings = FALSE)
dir.create(file.path(out, "tables"), recursive = TRUE, showWarnings = FALSE)
rd <- function(p) fread(p, sep = "\t", quote = "", na.strings = c("", "NA"))
pl <- function(n) readRDS(file.path("work/plots", paste0(n, ".rds")))
# Environmental Monitoring and Assessment artwork rules: no titles inside figures, sans-serif
# lettering 8–12 pt (Liberation Sans = Arial metrics), width <= 174 mm, height <= 234 mm,
# combination art (plots with text) as TIFF at 600 dpi; files named Fig1, Fig2, ...
FONT <- "Liberation Sans"
pub <- theme(plot.title = element_blank(), plot.subtitle = element_blank(),
             text = element_text(family = FONT, size = 9), axis.text = element_text(size = 8),
             legend.text = element_text(size = 8), strip.text = element_text(size = 9),
             plot.tag = element_text(size = 11, face = "bold"))
save_fig <- function(p, n, h_mm, w_mm = 174) {
  stopifnot(h_mm <= 234, w_mm <= 174)
  f <- file.path(out, "figures", paste0("Fig", n))
  ggsave(paste0(f, ".tif"), p, width = w_mm, height = h_mm, units = "mm", dpi = 600,
         device = function(filename, width, height, res, ...)
           grDevices::tiff(filename, width = width, height = height, units = "in", res = res,
                           compression = "lzw", type = "cairo", family = FONT))
  ggsave(paste0(f, ".png"), p, width = w_mm, height = h_mm, units = "mm", dpi = 300, bg = "white")
  ggsave(paste0(f, ".pdf"), p, width = w_mm, height = h_mm, units = "mm", device = cairo_pdf, family = FONT)
}
unlink(list.files(file.path(out, "figures"), full.names = TRUE))

# ---- Figures ----
# Numbered in order of first citation in the manuscript (step 16)
save_fig((pl("05_read_tracking") + pub) / (pl("05_rarefaction") + pub) + plot_annotation(tag_levels = "a"), 1, 185)
save_fig(pl("10_protein") + pub, 2, 160)
save_fig((pl("09_18S_roles") + pub) / (pl("09_COI_groups") + pub) + plot_annotation(tag_levels = "a"), 3, 165)
save_fig(pl("09_genera_heatmap") + pub, 4, 220)
save_fig((pl("08_alpha") + pub) / (pl("08_overlap") + pub) + plot_layout(heights = c(1, 1.2)) +
           plot_annotation(tag_levels = "a"), 5, 210)
save_fig(pl("11_rotifer_genera") + pub, 6, 100)
save_fig(pl("15_microscopy") + pub, 7, 85)

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
