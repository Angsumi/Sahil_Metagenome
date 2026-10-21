# Step 15 — Compare the DNA results for Deepor Beel (W2) with published microscopy surveys of the
# same lake (scripts/literature_deepor.tsv): rotifers from Sharma (2010) and algae from
# Baruah et al. (2020). Surveys differ in year, season and method, so this tests agreement of the
# species/genus lists, not abundances.
# Evidence levels for DNA detections: "named" = reference-library name (step 6); "provisional" =
# genus of the best GenBank DNA hit >= 80 % (step 7) or best protein hit >= 89 % with rotifer
# consensus (step 10).
suppressPackageStartupMessages({ library(data.table); library(ggplot2) })

out <- "results/15_microscopy"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
rd <- function(p) fread(p, sep = "\t", quote = "", na.strings = c("", "NA"))
lit <- rd("scripts/literature_deepor.tsv")

# ---- Rotifers detected in Deepor by DNA ----
coi <- rd("results/09_ecology/COI_asv_groups.tsv")
t18 <- rd("results/06_taxonomy/18S_taxonomy.tsv")
bl <- rd("results/06_taxonomy/COI_blast_unknowns_summary.tsv")
pr <- rd("results/10_protein/COI_protein_summary.tsv")
w2 <- coi[W2 > 0]
named_sp <- unique(gsub("_", " ", na.omit(w2[group == "Rotifers", Species])))
named_gen <- unique(c(na.omit(w2[group == "Rotifers", Genus]),
                      na.omit(t18[Class %in% "Rotifera" & W2 > 0, Genus])))
first_word <- function(x) sub(" .*", "", x)
prov_gen <- unique(c(
  first_word(bl[asv %in% w2$asv & ncbi_identity >= 80 & ncbi_phylum == "Rotifera" &
                  !grepl("environmental|sample", ncbi_best_hit), ncbi_best_hit]),
  first_word(pr[asv %in% w2$asv & aa_identity >= 89 & consensus_phylum %in% "Rotifera", best_hit])))
family_of <- c(Brachionus = "Brachionidae", Keratella = "Brachionidae", Plationus = "Brachionidae",
               Platyias = "Brachionidae", Anuraeopsis = "Brachionidae", Lecane = "Lecanidae",
               Asplanchna = "Asplanchnidae", Polyarthra = "Synchaetidae", Filinia = "Trochosphaeridae",
               Trichocerca = "Trichocercidae", Lepadella = "Lepadellidae", Colurella = "Lepadellidae",
               Euchlanis = "Euchlanidae", Mytilina = "Mytilinidae", Epiphanes = "Epiphanidae",
               Cephalodella = "Notommatidae", Proales = "Proalidae", Hexarthra = "Hexarthridae",
               Microcodon = "Microcodonidae")
dna_level <- function(level, name) {
  if (level == "species") return(if (name %in% named_sp) "named" else "not detected")
  gens <- if (level == "genus") name else names(family_of)[family_of == name]
  if (any(gens %in% named_gen)) "named" else if (any(gens %in% prov_gen)) "provisional" else "not detected"
}
rot <- lit[group == "Rotifera"]
rot[, dna_detection := mapply(dna_level, level, name)]
fwrite(rot[, .(level, name, note, dna_detection)], file.path(out, "rotifers_microscopy_vs_DNA.tsv"), sep = "\t")

dna_rot_gen <- sort(unique(c(named_gen, prov_gen)))
fwrite(data.table(genus = dna_rot_gen,
                  evidence = fifelse(dna_rot_gen %in% named_gen, "named", "provisional"),
                  in_microscopy_list = dna_rot_gen %in% rot[level == "genus", name]),
       file.path(out, "rotifer_genera_DNA_Deepor.tsv"), sep = "\t")

# ---- Algae: genera in Deepor by DNA (18S) vs Baruah et al. 2020 ----
roles <- rd("results/09_ecology/18S_asv_roles.tsv")
algal_roles <- c("Green algae", "Desmids & conjugating algae", "Diatoms", "Golden & other algae", "Dinoflagellates")
dna_alg <- roles[role %in% algal_roles & W2 > 0 & !is.na(Genus) & !grepl("aceae$|_X", Genus),
                 .(reads = sum(W2)), by = .(Genus, role)]
mic_alg <- lit[group == "Algae" & level == "genus", name]
alg <- merge(dna_alg[, .(genus = Genus, role, dna_reads = reads)], data.table(genus = mic_alg, microscopy = TRUE),
             by = "genus", all = TRUE)
alg[is.na(microscopy), microscopy := FALSE]
alg[, found_by := fcase(!is.na(dna_reads) & microscopy, "both", !is.na(dna_reads), "DNA only", default = "microscopy only")]
# Microscopy-only genera that 18S cannot (cyanobacteria: bacteria, no 18S gene) or rarely
# (euglenoids: divergent 18S, poorly amplified by V4 primers) detect
cyano <- c("Aphanocapsa", "Aulosira", "Chroococcus", "Cylindrospermum", "Merismopedia", "Microcystis", "Nostoc",
           "Oscillatoria", "Phormidium", "Pleurocapsa", "Spirulina")
eugl <- c("Euglena", "Gyropaigne", "Lepocinclis", "Phacus", "Strombomonas", "Trachelomonas")
alg[, note := fcase(genus %in% cyano, "cyanobacterium: no 18S gene, not detectable",
                    genus %in% eugl, "euglenoid: poorly amplified by 18S V4 primers", default = "")]
setorder(alg, found_by, -dna_reads, genus)
fwrite(alg, file.path(out, "algae_genera_microscopy_vs_DNA.tsv"), sep = "\t")

summ <- rbind(
  rot[, .(comparison = paste("Rotifer", level, "(Sharma 2010)"),
          microscopy = .N, also_by_DNA_named = sum(dna_detection == "named"),
          also_by_DNA_provisional = sum(dna_detection == "provisional")), by = level][, -"level"],
  data.table(comparison = "Algal genera (Baruah et al. 2020)", microscopy = length(mic_alg),
             also_by_DNA_named = alg[found_by == "both", .N], also_by_DNA_provisional = 0L))
summ[, DNA_only := c(NA, NA, NA, alg[found_by == "DNA only", .N])]
fwrite(summ, file.path(out, "comparison_summary.tsv"), sep = "\t")

# ---- Figure ----
pl <- melt(summ, id.vars = "comparison", measure.vars = c("also_by_DNA_named", "also_by_DNA_provisional"),
           variable.name = "evidence", value.name = "n")
pl[, missed := summ$microscopy[match(comparison, summ$comparison)] -
     ave(n, comparison, FUN = sum)]
pl <- rbind(pl[, .(comparison, evidence, n)],
            unique(pl[, .(comparison, evidence = "not detected by DNA", n = missed)]))
pl[, evidence := factor(evidence, levels = c("also_by_DNA_named", "also_by_DNA_provisional", "not detected by DNA"),
                        labels = c("also found by DNA (named)", "also found by DNA (provisional)", "not found by DNA"))]
pl[, comparison := factor(comparison, levels = rev(summ$comparison))]
p <- ggplot(pl, aes(n, comparison, fill = evidence)) +
  geom_col(width = 0.6, position = position_stack(reverse = TRUE)) +
  geom_text(aes(label = ifelse(n > 0, n, "")), position = position_stack(vjust = 0.5, reverse = TRUE),
            colour = "white", size = 3.4) +
  scale_fill_manual(values = c("#2b6c8f", "#7fb2cc", "#c9c9c9")) +
  labs(x = "Taxa recorded by microscopy in Deepor Beel", y = NULL, fill = NULL,
       title = "Does DNA find what microscopists found in Deepor Beel?") +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom", plot.title.position = "plot")
dir.create("work/plots", recursive = TRUE, showWarnings = FALSE)
saveRDS(p, "work/plots/15_microscopy.rds")
ggsave("docs/img/15_microscopy.png", p, width = 9.5, height = 4.2, dpi = 120)
print(rot[, .(level, name, dna_detection)]); print(summ); print(alg[found_by == "both"])
