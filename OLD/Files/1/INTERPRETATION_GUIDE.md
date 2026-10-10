# Eurofins NGS Result — Interpretation Guide

**Project:** Plankton diversity, Chandubi Beel and Deepor Beel
**Samples:** W1 = Chandubi Beel, W2 = Deepor Beel
**Guide prepared:** 1 August 2026

---

## 1. What this dataset actually is

Before anything else, be clear about what was sequenced, because it constrains every claim you can make.

**Marker:** COI (mitochondrial cytochrome oxidase I), **not 18S rRNA**. This was verified directly from the FASTQ files by four independent tests — see §1a below. The amplicon is the ~313 bp "Leray fragment" used in animal metabarcoding, generated with mlCOIintF (Leray et al. 2013) forward and HCO2198 (degenerate form) reverse.

**Platform:** Illumina MiSeq, 2 × 300 bp paired-end (run ID `M04635:72:000000000-MDYKK`).

**Pipeline:** QIIME 2. The exported visualisations carry QIIME 2 branding, and the feature IDs are MD5 hashes — the signature of DADA2 denoising into ASVs (amplicon sequence variants), not 97% OTUs.

**Reference database:** a COI animal reference. Every assignment sits under `k__Animalia`, and unresolved ranks are padded with `_X`, `_XX` suffixes. Ask Eurofins which database and version — probably MIDORI or a BOLD-derived set. You cannot write a methods section without this.

### The consequence you must not miss

COI primers amplify animals. Nothing else. **There is no phytoplankton in this dataset** — no diatoms, no green algae, no cyanobacteria, no ciliates or other protists. If your project was framed as "plankton diversity", these files cover the metazoan zooplankton component only. Phytoplankton would need a separate 18S/23S/rbcL or 16S run.

Say "zooplankton" or "metazoan plankton" everywhere in the write-up. Reviewers will catch "plankton" backed by COI data.

---

## 1a. Verification that this is COI

Run on 20,000 reads per file from `1_Data/2_HQ_Data`. All four tests agree.

**Test 1 — forward primer.** The most common first 26 bases of R1, in both samples:

```
GGTACTGGTTGAACTGTTTACCCTCC
GGTACTGGTTGAACTGTTTATCCTCC
GGTACAGGTTGAACTGTTTATCCTCC
GGTACTGGATGAACTGTTTATCCTCC
```

These are exact matches to **mlCOIintF** = `GGWACWGGWTGAACWGTWTAYCCYCC`, resolved at each degenerate site. Match rate: 72.4% (W1), 75.5% (W2).

**Test 2 — reverse primer.** The most common first 26 bases of R2:

```
TAAACTTCAGGGTGACCAAAGAATCA
TAAACTTCAGGGTGACCAAAAAATCA
TAAACTTCAGGGTGACCAAAGAACCA
```

These match **HCO2198** in its degenerate form (`TAAACYTCAGGRTGRCCAAARAAYCA`, dgHCO2198 / jgHCO2198 family) — the standard COI reverse primer, partner to mlCOIintF in the Leray protocol. Match rate: 83.4% (W1), 83.5% (W2).

**Test 3 — no rRNA primers present.** The same reads were screened against 515F/806R (16S V4), TAReuk454FWD1/TAReukREV3 (18S V4), 1391f/EukBr (18S V9), and ITS1F. **Zero hits for every one of them**, in both R1 and R2, in both samples. There is no 18S in these files.

**Test 4 — the sequences are protein-coding.** This is the decisive one. rRNA genes are not translated and show stop codons scattered evenly across all three reading frames. Protein-coding genes have exactly one clean frame. Translating the reads with the invertebrate mitochondrial code (NCBI transl_table 5):

| Reading frame | Mean stop codons per read | Reads with zero stops |
|---|---|---|
| +1 | 4.93 | 14.8% |
| **+2** | **1.05** | **80.0%** |
| +3 | 5.25 | 5.1% |

(W1; W2 is identical to two decimal places.) One frame is open in 80% of reads and the other two are closed. That is a protein-coding gene, not rRNA.

The frame also confirms the *mitochondrial* genetic code specifically: in-frame TGA codons occur at 0.67–0.78% of positions. Under the standard nuclear code TGA is a stop, and those reads would be excluded; under the invertebrate mitochondrial code it encodes tryptophan. AGA/AGG (serine in table 5, arginine in table 1) appear at 1.87%. GC content is 36.5%, typical of invertebrate mtDNA and far below the ~50% of eukaryotic 18S.

**One practical consequence:** the primers are still attached to the reads in `2_HQ_Data` — they were not trimmed. If you re-run DADA2 yourself, remove them with Cutadapt first, or the primer bases will be treated as biological sequence.

---

## 2. Folder-by-folder: what it is and how to open it

| Folder | Contents | Open with |
|---|---|---|
| `1_Data/1_Raw_Data` | Raw reads, `.fastq.gz`, 4 files | Don't open directly. FastQC / MultiQC for QC; archive for NCBI SRA submission |
| `1_Data/2_HQ_Data` | Quality-filtered reads, `.fq.gz` | Same. This is your input if you reprocess |
| `2_Analysis_Reports` | 3 Excel workbooks, 6 sheets each (Phylum → Species) | Excel / LibreOffice |
| `3_Piecharts` | Per-sample composition PNGs + separate legend PNGs | Any image viewer |
| `4_Feature_table` | `Feature_table.txt` — the ASV × sample count matrix | Excel, R, or Python. **This is the only file you can do real analysis on** |
| `5_Barplots` | Interactive QIIME 2 taxa-barplot + static PNGs + `level-1` … `level-7.csv` | `index.html` in a browser; CSVs in Excel/R |
| `6_Rarefaction_curve` | Observed-features rarefaction PNG | Image viewer |
| `7_Heatmap` | Taxa heatmap PNG | Image viewer |
| `8_Krona_charts` | Interactive Krona wheels; `W1.txt` / `W2.txt` are the raw input tables | `index.html` in a browser |

### Getting the interactive HTML files to work

`5_Barplots/index.html` and `8_Krona_charts/index.html` load data from sibling files. Two things break them:

1. **Moving the HTML out of its folder.** Keep the whole directory intact.
2. **Chrome's file:// restrictions.** Chrome often blocks the local data load and you get a blank page. Either open in Firefox, or serve the folder locally:

```bash
cd "5_Barplots"
python3 -m http.server 8000
# then visit http://localhost:8000 in any browser
```

Both charts have a `.qzv` original that Eurofins did not send. Ask for them — `.qzv` files open at https://view.qiime2.org and are far easier to cite and re-export.

---

## 3. Reading the files you'll actually use

### `2_Analysis_Reports/*.xlsx`

`W1_Analysis_Report.xlsx` and `W2_Analysis_Report.xlsx` give per-sample absolute read counts and percentages at six ranks. `Comparative_Analysis_Report.xlsx` puts the two side by side as percentages. Six sheets each: Phylum, Class, Order, Family, Genus, Species.

**"Other" is not a taxon.** It means the reads were classified only to the rank above and stopped. `Animalia / Other / Other / Other` = 17.9% of W1 is animal DNA that could not be placed even to phylum. Do not plot "Other" as if it were a group; report it as unassigned.

Likewise, `Brachionidae_X`, `Arachnida_XXX`, `Rotifera_XX` are placeholders, not names. `Brachionidae_X / Brachionidae_XX` means "a brachionid rotifer, genus and species unknown".

### `4_Feature_table/Feature_table.txt`

Tab-separated, with a `# Constructed from biom file` comment on line 1 — skip that line when importing.

```
#OTU ID    W1    W2    taxonomy
<md5 hash> 0.0   412.0 k__Animalia
```

272 ASVs. Import into R or Python and you can compute anything: diversity indices, ordination, differential abundance. The Excel reports are summaries of this file.

### `5_Barplots/level-*.csv`

Level 1 = kingdom through level 7 = species. Samples in rows, taxa in columns, raw counts. These are the tidiest inputs for R or MicrobiomeAnalyst. Note the trailing `BarcodeSequence` / `LinkerPrimerSequence` / `Description` metadata columns — drop them before analysis.

---

## 4. What your data says

### Sequencing effort

| | Chandubi (W1) | Deepor (W2) |
|---|---|---|
| Raw read pairs | 167,886 | 143,351 |
| After quality filtering | 136,274 | 115,745 |
| Reads in final ASV table | 69,975 | 56,262 |
| Retained from raw | 42% | 39% |
| ASVs | 169 | 105 |

The ~40% retention is normal for COI: read pairs are lost at merging, chimera removal, and length filtering. Nothing alarming, but get the DADA2 stats table from Eurofins so you can report the loss at each step.

The rarefaction curves both flatten well before final depth. **Sequencing depth was sufficient** — deeper sequencing would not have found many more ASVs. That is a clean, defensible statement.

### Diversity (computed from the feature table)

| Index | Chandubi (W1) | Deepor (W2) |
|---|---|---|
| Observed ASVs | 169 | 105 |
| Shannon (H′) | 4.48 | 4.23 |
| Simpson (1−D) | 0.986 | 0.983 |
| Inverse Simpson | 70.5 | 60.2 |
| Pielou's evenness (J′) | 0.874 | 0.909 |

Chandubi carries more ASVs and higher Shannon diversity. Deepor is slightly more even — fewer types, but distributed a bit more equally, which fits its stronger single-genus dominance (*Keratella* + *Brachionus* together are 25% of Deepor versus 13% of Chandubi).

With one sample per lake, **these are descriptions, not results.** You cannot test whether the difference is significant. See §5.

### Composition

| Phylum | Chandubi (W1) | Deepor (W2) |
|---|---|---|
| Rotifera | 42.4% | 54.2% |
| Arthropoda | 39.7% | 29.9% |
| Unassigned (kingdom only) | 17.9% | 15.9% |
| Gastrotricha | 0.03% | 0% |

Rotifers dominate both, more so at Deepor. Within them, Ploima and family Brachionidae carry nearly everything: Brachionidae is 30.8% of Chandubi and 46.0% of Deepor.

Named species reaching >1% in either lake:

| Species | Chandubi | Deepor |
|---|---|---|
| *Keratella tropica* | 6.19% | 14.89% |
| *Brachionus caudatus* | 4.97% | 10.52% |
| *Euchlanis deflexa* | 4.40% | 1.85% |
| *Brachionus elevatus* | 1.11% | 2.93% |
| *Polyarthra vulgaris* | 1.93% | 1.25% |

*Keratella tropica* and *Brachionus caudatus* are both pantropical eutrophic-water indicators. Their much higher share at Deepor is worth discussing against Deepor Beel's known nutrient loading and encroachment pressure — but discuss it as consistent with, not as evidence of, eutrophication. One sample cannot establish that.

The Arthropoda signal is mostly Arachnida (14.6% / 10.8%), and within that Trombidiformes — **water mites, not crustaceans**. Insecta is 4.6% / 2.7%, which is drifting larvae or terrestrial contamination rather than true plankton.

### The gap you have to address

**There are zero copepods and zero cladocerans in this dataset.** Not low — absent. A search of all 272 ASVs for Copepoda, Cladocera, Branchiopoda, Hexanauplia, *Daphnia*, *Moina*, *Cyclops*, or *Diaptomus* returns nothing.

That is biologically impossible for two Assamese floodplain wetlands. Copepods and cladocerans are the backbone of tropical freshwater zooplankton. So they are hiding in the unassigned fraction:

| Bucket | ASVs | Chandubi reads | Deepor reads |
|---|---|---|---|
| `Arthropoda`, no class assigned | 72 | 14,331 (20.5%) | 9,223 (16.4%) |
| `Animalia` only | 50 | 12,501 (17.9%) | 8,954 (15.9%) |
| **Combined unidentified** | **122** | **38.4%** | **32.3%** |

Roughly a third of your reads, and 45% of your ASVs, are unidentified — and the largest single block of them is unplaced Arthropoda. Those are almost certainly your crustacean zooplankton, unassigned because the COI reference database has poor coverage of Indian freshwater crustaceans.

This is fixable and it is the highest-value thing you can do with this data:

1. Get the representative sequences (`rep-seqs.qza` or a FASTA) from Eurofins. Without them you can do nothing here.
2. BLAST the abundant unassigned ASVs against NCBI nt and BOLD.
3. Anything that comes back as *Mesocyclops*, *Thermocyclops*, *Diaphanosoma*, *Moina*, *Ceriodaphnia* and the like gets reported, with the % identity stated.

Recovering the crustacean fraction turns a thin result into a publishable one.

---

## 5. Four limitations to sort out before you write

**5.1 One sample per lake means no statistics.** n = 1 per site. You cannot run PERMANOVA, t-tests, ANCOM, LEfSe, or anything inferential, and you cannot say a difference between the lakes is significant. If you have field replicates or seasonal samples that weren't sequenced, sequencing them is the single biggest improvement available. If not, the paper is a descriptive baseline inventory — which is legitimate and publishable for these two wetlands, but must be framed that way.

**5.2 The two samples share almost no ASVs.** Only 2 of 272 ASVs occur in both lakes (Jaccard similarity 0.007; Bray–Curtis dissimilarity 0.976). Taken at face value that means the two communities have essentially nothing in common — which contradicts the taxonomy, where both lakes are dominated by the same *Keratella tropica* and *Brachionus caudatus*.

The likely explanation is that the two samples were denoised separately, or trimmed to different lengths, so the same organism received a different ASV hash in each sample. **Ask Eurofins whether DADA2 was run jointly on both samples.** If it wasn't, the feature table cannot be used for any ASV-level comparison — beta diversity, ordination, shared/unique Venn diagrams are all invalid. You would need to re-run DADA2 on both samples together from the HQ FASTQs. Genus- and species-level comparisons from the Excel reports are unaffected.

**5.3 Read counts are not abundance.** COI copy number varies by orders of magnitude across taxa, and body size, gut contents, and primer mismatch all bias recovery. A rotifer-dominated read profile does not mean rotifer-dominated biomass. Report relative read abundance, and if you have microscope counts from the same samples, present both — the comparison is often the most interesting part of a metabarcoding paper.

**5.4 No negative or positive controls in the delivery.** Ask whether extraction blanks, PCR blanks, or a mock community were run. Without them you cannot rule out contamination, and the Insecta reads in particular are suspect.

---

## 6. Software

### To just look at what you have

- **Excel / LibreOffice Calc** — the three `.xlsx` reports and the `level-*.csv` files.
- **Firefox** — the two interactive `index.html` files. Firefox handles local file loads better than Chrome here.

### To do your own analysis (no coding)

- **MicrobiomeAnalyst** (https://www.microbiomeanalyst.ca) — free, web-based, purpose-built. Upload `level-7.csv` or the feature table plus a small metadata file and it produces diversity indices, ordination, and heatmaps. Best starting point if you don't want to write code.
- **PAST** (https://past.en.lo4d.com) — free desktop stats package, standard in ecology. Good for diversity indices and similarity measures from a pasted count matrix.
- **Krona** (KronaTools) — if you want to rebuild the interactive wheels: `ktImportText 8_Krona_charts/W1.txt -o W1.html`

### To do it properly (R)

The standard stack:

```r
install.packages(c("vegan", "ggplot2", "tidyverse", "pheatmap"))
BiocManager::install(c("phyloseq", "microbiome"))
```

- **phyloseq** — holds the feature table, taxonomy, and metadata as one object; handles all the bookkeeping.
- **vegan** — diversity indices, rarefaction, distance matrices, ordination (NMDS/PCoA), PERMANOVA.
- **microbiome** — convenience wrappers for composition plots and core taxa.
- **ggplot2** — publication figures. Regenerate the barplots and heatmap yourself so you control the colours, fonts, and taxon selection; the vendor PNGs are not journal-quality.

### To reprocess from the FASTQs

- **QIIME 2** (2024.10 or later) — install via conda, Docker, or WSL2 on Windows. Needed if you re-run DADA2 jointly (see §5.2) or re-assign taxonomy against a better reference.
- **FastQC + MultiQC** — verify the raw and HQ read quality yourself rather than taking the vendor's word.
- **Cutadapt** — check that primers were actually removed. They appear to still be present at the 5′ end of the HQ reads, which matters if you re-denoise.
- **BLAST+ or NCBI web BLAST, and BOLD Systems** (https://boldsystems.org) — for the unassigned ASV work in §4.

Windows note: QIIME 2 needs WSL2 or Docker. macOS and Linux install natively via conda.

---

## 7. What to request from Eurofins

Send one email asking for all of it:

1. **`rep-seqs.qza` or a FASTA of representative sequences** — without this you cannot BLAST the unassigned ASVs, and that is where your crustaceans are. Highest priority.
2. **The `.qza` and `.qzv` artifacts** — feature table, taxonomy, barplot, Krona, rarefaction. These carry the full provenance record and open at view.qiime2.org.
3. **Full methods:** exact primer pair (forward and reverse), DNA extraction kit, PCR conditions and cycle number, DADA2 truncation and trimming parameters, and whether the two samples were denoised together or separately.
4. **The DADA2 stats table** — reads in, filtered, denoised, merged, non-chimeric, per sample.
5. **Reference database name and version**, and the classifier used (naive Bayes, VSEARCH, BLAST) with its confidence threshold.
6. **Control samples** — whether blanks or a mock community were sequenced, and their results.

Items 1 and 3 are the ones that block your analysis. The rest you need for the methods section regardless.

---

## 8. Suggested order of work

1. Email Eurofins (§7).
2. Open the interactive barplot and Krona charts, get familiar with what's there.
3. Import `Feature_table.txt` into R or MicrobiomeAnalyst; reproduce the diversity numbers in §4 yourself.
4. When the rep-seqs arrive, BLAST the top ~30 unassigned ASVs. Expect this to change your species list substantially.
5. Decide whether you can get more samples sequenced. If yes, hold the write-up. If no, frame the paper as a descriptive baseline and be explicit about n = 1 per site.
6. Rebuild the figures in ggplot2 for publication.
