# Step 9 — Ecological reading of the named community.
#  (a) 18S reads grouped by ecological role (algae by type, fungi, water moulds,
#      protozoa, parasites, animals).
#  (b) COI reads grouped by animal group, using the reference-library name where
#      available and the NCBI BLAST phylum (>= 80 % identity) for the 40 looked-up unknowns.
#  (c) Heatmap of the most abundant named genera from both markers.
#  (d) Marker complementarity: which animal genera each barcode detected.
#  (e) Indicator taxa: genera/species commonly used as water-quality indicators, with
#      their share in each lake. Interpretation notes are general, not site-specific evidence.
dir.create("work/plots", recursive = TRUE, showWarnings = FALSE)
suppressPackageStartupMessages({ library(data.table); library(ggplot2) })

out <- "results/09_ecology"
dir.create(out, recursive = TRUE, showWarnings = FALSE)
site_of <- c(W1 = "Chandubi (W1)", W2 = "Deepor Beel (W2)")
t18 <- fread("results/06_taxonomy/18S_taxonomy.tsv", sep = "\t", quote = "", na.strings = c("", "NA"))
tco <- fread("results/06_taxonomy/COI_taxonomy.tsv", sep = "\t", quote = "", na.strings = c("", "NA"))
blast <- fread("results/06_taxonomy/COI_blast_unknowns_summary.tsv", sep = "\t", quote = "",
               na.strings = c("", "NA"))
pct <- function(x) 100 * x / sum(x)

# ---- (a) 18S ecological roles ----
diatoms <- c("Mediophyceae", "Coscinodiscophyceae", "Bacillariophyceae")
other_algae <- c("Chrysophyceae", "Eustigmatophyceae", "Xanthophyceae")
protozoa <- c("Rhizaria-Cercozoa", "Alveolata-Ciliophora", "Stramenopiles-Bigyra", "Tubulinea", "Evosea",
              "Opisthokonta-Choanoflagellata", "Centroplasthelida", "Ancyromonadida", "Rigifilida",
              "Alveolata-Chrompodellids")
parasites <- c("Alveolata-Perkinsea", "Alveolata-Apicomplexa", "Opisthokonta-Ichthyosporea")
t18[, role := fcase(
  Division == "Chlorophyta", "Green algae",
  Division == "Streptophyta" & Class == "Zygnemophyceae", "Desmids & conjugating algae",
  Division == "Streptophyta", "Plants",
  Class %in% diatoms, "Diatoms",
  Class %in% other_algae | Division %in% c("Glaucophyta", "Cryptophyta", "Haptophyta", "Rhodophyta"),
    "Golden & other algae",
  Division == "Alveolata-Dinoflagellata", "Dinoflagellates",
  Division == "Opisthokonta-Fungi", "Fungi",
  Class %in% c("Peronosporomycetes", "Hyphochytriomyceta"), "Water moulds (oomycetes)",
  Division %in% protozoa, "Protozoa (free-living)",
  Division %in% parasites, "Parasitic protists",
  Division == "Opisthokonta-Metazoa", "Animals",
  default = "Unassigned / other")]
roles <- t18[, .(W1 = sum(W1), W2 = sum(W2)), by = role][, `:=`(W1 = round(pct(W1), 2), W2 = round(pct(W2), 2))]
role_levels <- c("Green algae", "Desmids & conjugating algae", "Diatoms", "Golden & other algae", "Dinoflagellates",
                 "Plants", "Protozoa (free-living)", "Parasitic protists", "Fungi", "Water moulds (oomycetes)",
                 "Animals", "Unassigned / other")
roles <- roles[order(match(role, role_levels))]
fwrite(roles, file.path(out, "18S_ecological_roles.tsv"), sep = "\t")
fwrite(t18[, .(asv, W1, W2, role, Division, Class, Genus, Species)], file.path(out, "18S_asv_roles.tsv"), sep = "\t")

role_cols <- c("Green algae" = "#3f8f4f", "Desmids & conjugating algae" = "#8cc084", "Diatoms" = "#c9a227",
               "Golden & other algae" = "#e3c770", "Dinoflagellates" = "#d08a4a", "Plants" = "#5b6b2f",
               "Protozoa (free-living)" = "#4f8fb8", "Parasitic protists" = "#8a6bb0", "Fungi" = "#b5536b",
               "Water moulds (oomycetes)" = "#d98aa0", "Animals" = "#2b4c6f", "Unassigned / other" = "#dcdcdc")
rl <- melt(roles, id.vars = "role", variable.name = "sample", value.name = "pct")
rl[, site := site_of[sample]][, role := factor(role, levels = rev(role_levels))]
p1 <- ggplot(rl, aes(pct, site, fill = role)) +
  geom_col(width = 0.55, colour = "white", linewidth = 0.3) +
  scale_fill_manual(values = role_cols, breaks = role_levels) +
  scale_x_continuous(labels = function(x) paste0(x, "%"), expand = c(0, 0)) +
  labs(x = "Share of 18S reads", y = NULL, fill = NULL,
       title = "Who does what: the microscopic community by ecological role (18S)") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "bottom", plot.title.position = "plot") + guides(fill = guide_legend(ncol = 3))
saveRDS(p1, "work/plots/09_18S_roles.rds")
ggsave("docs/img/09_18S_roles.png", p1, width = 10, height = 4.6, dpi = 120)

# ---- (b) COI animal groups (library + BLAST) ----
bl <- blast[ncbi_identity >= 80, .(asv, blast_phylum = ncbi_phylum, blast_class = ncbi_class)]
tco <- merge(tco, bl, by = "asv", all.x = TRUE)
tco[, phylum_final := fifelse(!is.na(Phylum), Phylum, blast_phylum)]
tco[, class_final := fifelse(!is.na(Class), Class, blast_class)]
tco[, group := fcase(
  phylum_final == "Rotifera", "Rotifers",
  phylum_final == "Arthropoda" & (grepl("Hexanauplia|Copepoda", class_final) | Genus %in% "Mesocyclops"), "Copepods",
  phylum_final == "Arthropoda" & class_final %in% "Ostracoda", "Ostracods",
  phylum_final == "Arthropoda", "Insects, mites & other arthropods",
  phylum_final %in% c("Nemertea", "Nematoda", "Mollusca", "Annelida", "Gastrotricha", "Platyhelminthes", "Metazoa"),
    "Other animals (worms etc.)",
  !is.na(phylum_final), "Non-animal (algae, fungi, bacteria…)",
  Kingdom %in% "Metazoa", "Animal, group unknown",
  default = "Unknown")]
grp <- tco[, .(W1 = sum(W1), W2 = sum(W2)), by = group][, `:=`(W1 = round(pct(W1), 2), W2 = round(pct(W2), 2))]
grp_levels <- c("Rotifers", "Copepods", "Ostracods", "Insects, mites & other arthropods", "Other animals (worms etc.)",
                "Animal, group unknown", "Non-animal (algae, fungi, bacteria…)", "Unknown")
grp <- grp[order(match(group, grp_levels))]
fwrite(grp, file.path(out, "COI_animal_groups.tsv"), sep = "\t")
fwrite(tco[, .(asv, W1, W2, group, phylum_final, class_final, Genus, Species, identity)],
       file.path(out, "COI_asv_groups.tsv"), sep = "\t")

grp_cols <- c("Rotifers" = "#2b6c8f", "Copepods" = "#c2662d", "Ostracods" = "#e0a35a",
              "Insects, mites & other arthropods" = "#8a6bb0", "Other animals (worms etc.)" = "#5a9e6f",
              "Animal, group unknown" = "#9fb7c6", "Non-animal (algae, fungi, bacteria…)" = "#c9a227",
              "Unknown" = "#dcdcdc")
gl <- melt(grp, id.vars = "group", variable.name = "sample", value.name = "pct")
gl[, site := site_of[sample]][, group := factor(group, levels = rev(grp_levels))]
p2 <- ggplot(gl, aes(pct, site, fill = group)) +
  geom_col(width = 0.55, colour = "white", linewidth = 0.3) +
  scale_fill_manual(values = grp_cols, breaks = grp_levels) +
  scale_x_continuous(labels = function(x) paste0(x, "%"), expand = c(0, 0)) +
  labs(x = "Share of COI reads", y = NULL, fill = NULL,
       title = "Zooplankton by group (COI, reference library + GenBank look-up)") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "bottom", plot.title.position = "plot") + guides(fill = guide_legend(ncol = 3))
saveRDS(p2, "work/plots/09_COI_groups.rds")
ggsave("docs/img/09_COI_groups.png", p2, width = 10, height = 4.4, dpi = 120)

# ---- (c) heatmap of top genera, both markers ----
gen <- rbind(t18[!is.na(Genus), .(marker = "18S", Genus, W1, W2, role)],
             tco[!is.na(Genus), .(marker = "COI", Genus, W1, W2, role = group)])
tot <- list(`18S` = c(W1 = sum(t18$W1), W2 = sum(t18$W2)), COI = c(W1 = sum(tco$W1), W2 = sum(tco$W2)))
gen[, `:=`(W1p = 100 * W1 / tot[[marker]][["W1"]], W2p = 100 * W2 / tot[[marker]][["W2"]]), by = marker]
g <- gen[, .(W1 = sum(W1p), W2 = sum(W2p), role = role[1]), by = .(marker, Genus)]
topg <- g[order(-(pmax(W1, W2)))][1:30]
fwrite(topg[, `:=`(W1 = round(W1, 3), W2 = round(W2, 3))], file.path(out, "top_genera.tsv"), sep = "\t")
hm <- melt(topg, id.vars = c("marker", "Genus", "role"), measure.vars = c("W1", "W2"),
           variable.name = "sample", value.name = "pct")
hm[, site := factor(site_of[sample], levels = site_of)]
hm[, lab := sprintf("%s  (%s · %s)", gsub("_", " ", Genus), marker, role)]
ord <- topg[order(W1 - W2), sprintf("%s  (%s · %s)", gsub("_", " ", Genus), marker, role)]
hm[, lab := factor(lab, levels = ord)]
p3 <- ggplot(hm, aes(site, lab, fill = pmax(pct, 0.001))) +
  geom_tile(colour = "white", linewidth = 0.6) +
  geom_text(aes(label = ifelse(pct >= 0.01, sprintf("%.2f", pct), "–"),
                colour = ifelse(pct >= 0.5, "white", "black")), size = 3.1) +
  scale_colour_identity() +
  scale_fill_gradientn(colours = c("#f7f7f2", "#cfe3ec", "#7fb2cc", "#2b6c8f", "#163e57"), trans = "log10",
                       labels = function(x) paste0(x, "%"), name = "% of reads") +
  scale_x_discrete(position = "top") +
  labs(x = NULL, y = NULL, title = "The 30 most abundant named genera",
       subtitle = "% of all reads of that barcode in each lake. Top: Chandubi-leaning; bottom: Deepor-leaning") +
  theme_minimal(base_size = 11) + theme(panel.grid = element_blank(), plot.title.position = "plot")
saveRDS(p3, "work/plots/09_genera_heatmap.rds")
ggsave("docs/img/09_genera_heatmap.png", p3, width = 9, height = 9.5, dpi = 120)

# ---- (d) marker complementarity for animals ----
a18 <- t18[Division == "Opisthokonta-Metazoa" & !is.na(Genus), .(phylum = na.omit(Class)[1]), by = Genus]
aco <- tco[Kingdom %in% "Metazoa" & !is.na(Genus), .(phylum = na.omit(Phylum)[1]), by = Genus]
comp <- merge(a18[, .(Genus, phylum_18S = phylum, in_18S = TRUE)], aco[, .(Genus, phylum_COI = phylum, in_COI = TRUE)],
              by = "Genus", all = TRUE)
comp[is.na(in_18S), in_18S := FALSE][is.na(in_COI), in_COI := FALSE]
comp[, group := fifelse(!is.na(phylum_18S), phylum_18S, phylum_COI)]
comp[, detected_by := fcase(in_18S & in_COI, "both", in_18S, "18S only", default = "COI only")]
fwrite(comp[order(detected_by, group, Genus), .(Genus, group, detected_by)], file.path(out, "animal_genera_by_marker.tsv"), sep = "\t")
phyla <- rbind(t18[Division == "Opisthokonta-Metazoa" & !is.na(Class), .(marker = "18S", phylum = Class, W1, W2)],
               tco[!is.na(phylum_final) & !group %in% c("Non-animal (algae, fungi, bacteria…)", "Unknown"),
                   .(marker = "COI", phylum = phylum_final, W1, W2)])
fwrite(phyla[, .(asvs = .N, reads = sum(W1 + W2)), by = .(phylum, marker)][order(phylum, marker)],
       file.path(out, "animal_phyla_by_marker.tsv"), sep = "\t")

# ---- (e) indicator taxa ----
ind <- fread("scripts/indicator_taxa.tsv", sep = "\t", quote = "")
lookup <- function(level, name, marker) {
  d <- if (marker == "18S") t18 else tco
  hit <- d[[level]] %in% name
  c(W1 = 100 * sum(d$W1[hit]) / sum(d$W1), W2 = 100 * sum(d$W2[hit]) / sum(d$W2))
}
ind_res <- rbindlist(lapply(seq_len(nrow(ind)), function(i) {
  v <- lookup(ind$level[i], ind$name[i], ind$marker[i])
  data.table(ind[i], chandubi_pct = round(v[["W1"]], 3), deepor_pct = round(v[["W2"]], 3))
}))
fwrite(ind_res, file.path(out, "indicator_taxa.tsv"), sep = "\t")

print(roles); print(grp); print(comp[, .N, by = detected_by]); print(ind_res[, .(name, marker, chandubi_pct, deepor_pct)])
