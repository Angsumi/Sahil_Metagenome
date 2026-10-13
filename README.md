# 🧬 Sahil_Metagenome

eDNA metabarcoding of plankton in two wetlands of Assam, India — **Chandubi Beel (W1)** and **Deepor Beel (W2, Ramsar site)** — using two markers:

- **18S rRNA V4** (E572F / E1009R) — micro-eukaryotes: algae, protists, fungi, small metazoans
- **COI** Leray fragment (mlCOIintF / jgHCO2198) — metazoan zooplankton

Illumina MiSeq 2 × 301 bp, one sample per site per marker.

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
│   ├── 06_build_site.py      # builds docs/index.html
│   └── run_all.sh            # runs everything
├── results/                  # Tables and ASV FASTA files from each step
├── docs/                     # GitHub Pages site
└── environment.yml           # conda/micromamba environment
```

## Reproduce

```bash
micromamba create -f environment.yml
micromamba run -n metabar bash scripts/run_all.sh
```

Intermediate FASTQs are written to `work/` (git-ignored).

## Status

- [x] Processing: QC → primer removal → DADA2 (joint) → ASV curation
- [ ] Taxonomic assignment (18S: PR2; COI: MIDORI2 / BOLD + BLAST of unassigned ASVs)
- [ ] Diversity and composition analysis
