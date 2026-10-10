# 🧬 Sahil_Metagenome

Metabarcoding and environmental metagenomics analysis repository for **Deepor Beel** and **Chandubi Lake** (Assam, India).

Investigates eukaryotic and prokaryotic micro-ecological biodiversity across freshwater ecosystems using **18S rRNA** and **COI (Cytochrome c Oxidase I)** amplicon sequencing pipelines.

---

## 📂 Repository Architecture

```text
Sahil_Metagenome/
├── NEW/
│   ├── 18S/                     # 18S rRNA Amplicon Metabarcoding
│   │   ├── Chandubi/            # Chandubi lake samples (W1_R1, W1_R2)
│   │   ├── Dipor Beel/          # Deepor Beel wetland samples (W2_R1, W2_R2)
│   │   └── MD5SUM_Raw.txt       # Raw fastq integrity checksums
│   │
│   └── COI/                     # Cytochrome c Oxidase I (COI) Amplicon Sequencing
│       ├── Chandubi/            # Chandubi lake samples
│       ├── Dipor Beel/          # Deepor Beel wetland samples
│       └── MD5SUM_Raw.txt       # Raw fastq integrity checksums
│
└── OLD/
    ├── Files-20261003T144336Z-1-001.zip  # Canonical raw archive (tracked via Git LFS)
    └── Files/
        ├── 1/                   # Dataset run 1 (1_Raw_Data, 2_HQ_Data, 2_Analysis_Reports, Barplots, Krona, Rarefaction, Heatmap)
        ├── 2/                   # Dataset run 2 (1_Raw_Data, 2_HQ_Data, 2_Analysis_Reports, Barplots, Krona, Rarefaction, Heatmap)
        ├── Analysis_and_Manuscript/      # Research manuscript drafts, comparative spreadsheets, 300 DPI publication figures
        ├── Claude outputs/               # Statistical synthesis & manuscript deliverables
        └── Literature_and_Article_Plan.md # Research design, literature review, and sequencing protocols
```

---

## 🔬 Study Focus & Locations
- **Deepor Beel (W2)**: A designated Ramsar wetland on the southwestern edge of Guwahati, Assam, characterized by diverse aquatic macrophytes and rich avifaunal habitat.
- **Chandubi Lake (W1)**: A natural tectonic lake located at the base of the Garo Hills in Kamrup district, Assam.

---

## 🛠️ Methods & Pipelines
- **Sequencing Targets**: 18S rRNA (eukaryotic microbial diversity) & COI (metazoan/invertebrate diversity).
- **Bioinformatics Engine**: QIIME 2 / DADA2 quality filtering, feature clustering, taxonomic assignment against Silva/NCBI/BOLD databases.
- **Visualizations**: Krona interactive taxonomic charts, rarefaction curves, hierarchical heatmaps, and relative abundance stacked barplots.
