# 🧬 Sahil_Metagenome

eDNA metabarcoding of plankton in two wetlands of Assam, India — **Chandubi Beel (W1)** and **Deepor Beel (W2, Ramsar site)** — using two markers:

- **18S rRNA V4** (E572F / E1009R) — micro-eukaryotes: algae, protists, fungi, small metazoans
- **COI** Leray fragment (mlCOIintF / jgHCO2198) — metazoan zooplankton

Illumina MiSeq 2 × 301 bp, one sample per site per marker, collected 29 March 2026 (Chandubi Beel 25.881015° N, 91.422898° E; Deepor Beel 26.10953° N, 91.70818° E).

Raw reads: NCBI BioProject [PRJNA1551452](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1551452) (BioSamples SAMN64467025, SAMN64467026).

**📄 Processing report (scripts, results and figures for every step): https://angsumi.online/Sahil_Metagenome/**

---

## Repository layout

```text
Sahil_Metagenome/
├── NEW/                      # Raw reads (MD5-verified)
│   ├── 18S/{Chandubi,Dipor Beel}/W*_R{1,2}.fastq.gz
│   └── COI/{Chandubi,Dipor Beel}/W*_R{1,2}.fastq.gz
├── scripts/                  # Pipeline, one script per step
│   ├── 01_qc.sh              # checksums, FastQC/MultiQC, read stats, quality profiles
│   ├── 02_primer_removal.sh  # Cutadapt, anchored primers, discard pairs without primers
│   ├── 03_dada2.R            # filter, learn errors, joint (pooled) denoising, merge, chimeras
│   ├── 04_asv_curation.R     # COI reading-frame/stop-codon filter, 18S length filter
│   ├── 05_summary.R          # read tracking, ASVs per site, rarefaction
│   ├── 06_taxonomy.sh/.R     # SINTAX naming vs PR2 (18S) and CO1 Reference Set (COI)
│   ├── 06b_blast_unknowns.sh # NCBI BLAST of abundant unnamed COI ASVs
│   ├── 08_diversity.R        # alpha diversity (rarefied, Hill numbers), overlap by level
│   ├── 09_ecology.R          # ecological roles, zooplankton groups, genera heatmap, indicators
│   ├── indicator_taxa.tsv    # indicator taxa list used by step 9
│   ├── 10_protein_search.sh  # protein-level (DIAMOND blastx) identification of unknown COI ASVs
│   ├── 11_rotifer_index.sh/.R# 97 % MOTUs and the Brachionus:Trichocerca index (QB/T)
│   ├── 12_manuscript.R       # publication figures, tables, supplementary workbook
│   ├── 13_sra_prep.py        # NCBI BioSample / SRA sheets and upload file names
│   ├── 14_verify_references.py # checks every reference against Crossref
│   ├── 15_microscopy_comparison.R # DNA vs published microscopy surveys of Deepor Beel
│   ├── literature_deepor.tsv # taxa listed by those surveys
│   ├── 16_manuscript_docx.js # Word manuscript formatted for Environmental Monitoring and Assessment
│   ├── 99_build_site.py      # builds docs/index.html
│   └── run_all.sh            # runs everything
├── results/                  # Tables and ASV FASTA files from each step
│   ├── 12_manuscript/        # Manuscript_EMAS.docx, figures (TIFF 600 dpi), tables
│   └── 13_sra/               # SRA submission sheets
├── docs/                     # GitHub Pages site
└── environment.yml           # conda/micromamba environment
```

## Reproduce

```bash
micromamba create -f environment.yml
micromamba run -n metabar bash scripts/run_all.sh
```

Intermediate FASTQs and reference databases are written to `work/` (git-ignored).

## Status

- [x] Processing: QC → primer removal → DADA2 (joint) → ASV curation
- [x] Taxonomic assignment (18S: PR2 v5.1.1; COI: Eukaryote CO1 Reference Set v5.1.0) + NCBI BLAST of unassigned COI ASVs
- [x] Diversity, composition, ecological roles, indicator taxa, marker complementarity
- [x] Protein-level identification of unknowns, rotifer trophic index (QB/T)
- [x] Manuscript package (`results/12_manuscript/`) and SRA sheets (`results/13_sra/`)
- [x] References verified against Crossref (`results/14_references/`); comparison with published microscopy (`results/15_microscopy/`)
- [x] Manuscript formatted for Environmental Monitoring and Assessment (`results/12_manuscript/Manuscript_EMAS.docx`)
- [x] Sampling date, coordinates and NCBI BioProject/BioSamples added
- [ ] Authors: co-authors, ORCID, acknowledgements, funding statements
