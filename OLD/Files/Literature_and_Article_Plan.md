# Related literature and article plan — Deepor Beel vs Chandubi Beel plankton metabarcoding

Prepared 11 September 2026. This reads your delivered Eurofins data (COI and 18S), matches it to published studies, and maps both onto a manuscript you can realistically write.

---

## 1. What you actually have, and what it lets you claim

Two marker datasets have arrived, one sample per lake in each:

**COI (folder 1) — the metazoan zooplankton.** 169 ASVs at Chandubi (W1), 105 at Deepor (W2). Rotifers dominate both (42% Chandubi, 54% Deepor), led by *Keratella tropica* and *Brachionus caudatus*, both pantropical eutrophic-water indicators and both markedly higher at Deepor. The arthropod signal is mostly water mites, not crustaceans. Critically, copepods and cladocerans are absent from the identified fraction — they are almost certainly sitting in the ~30% of reads the COI reference database could not place. BLASTing those unassigned ASVs is the single highest-value step you can take.

**18S rRNA (folder 2) — the micro-eukaryote community, phytoplankton included.** 422 ASVs. This is where your primary producers and protists are: diatoms (Diatomea), green algae (Chlorophyta), dinoflagellates, chrysophytes, ciliates, cercozoans, plus rotifers and nematodes. The two lakes look very different here — Chandubi carries abundant diatoms and green algae, Deepor is heavy in nematodes and oomycetes with almost no diatoms. This dataset is what lets you legitimately say "plankton" rather than only "zooplankton".

**Chloroplast 16S — not in this delivery.** When it arrives it will give you a cleaner, higher-resolution phytoplankton/cyanobacteria read to cross-check against the 18S algae.

**The hard constraint: n = 1 per lake.** With a single sample per site you cannot run PERMANOVA, ANOSIM, t-tests, or any significance test on the between-lake difference, and the separately-denoised feature tables make ASV-level beta diversity unreliable. This is not fatal, but it decides the kind of paper this is: **a descriptive, multi-marker baseline inventory of two contrasting Assam wetlands**, with between-lake differences reported as patterns consistent with known pressures, not as statistically demonstrated effects. Every strong paper below that *does* run statistics has either seasonal or spatial replication — that is the gap to be honest about, and the thing to fix if you can sequence more samples.

---

## 2. Related papers, grouped by the part of your paper each one helps you write

Verification status is marked on each: **[verified]** = I opened it and confirmed title/DOI/design; **[check]** = from search metadata, confirm the DOI resolves before citing (per your standing rule, don't cite any of the [check] items until the link is confirmed).

### A. Closest whole-study analogues — read these first for structure

- **DNA metabarcoding of zooplankton communities: species diversity and seasonal variation revealed by 18S rRNA and COI.** PeerJ, 2021. DOI 10.7717/peerj.11057. **[verified design; confirm author list]** This is the closest match to your markers — the same 18S V4 + COI pairing on freshwater zooplankton, Sanmenxia Reservoir. Use it as your methods and results skeleton: how they present per-marker taxonomy, Shannon/ACE, PCoA, and marker complementarity. Note what you *can't* copy: they had 9 sites × 4 seasons, so their PERMANOVA/ANOSIM/CCA are available to them and not to you.

- **Seasonal and Spatiotemporal Dynamics of Plankton Communities Using eDNA Metabarcoding in Singal Reservoir.** Environmental Management 76:92, 2026. DOI 10.1007/s00267-025-02357-1. **[verified]** South Korea (not India — I checked), 18S V9. Good model for framing plankton eDNA against environmental gradients and for how PERMANOVA + Spearman are reported. Again, their replication is what powers the stats.

### B. Justifying the multi-marker design (Introduction + Methods)

- **Metabarcoding using multiplexed markers increases species detection in complex zooplankton communities.** PubMed 30459837. **[check]** The citation to support "we used more than one marker because no single marker recovers the whole community" — exactly your COI-misses-algae, 18S-misses-resolution situation.
- **Multi-marker metabarcoding approach to study mesozooplankton at basin scale.** Scientific Reports 8, 2018. DOI 10.1038/s41598-018-30157-7. **[check]** Multi-marker rationale and per-marker taxonomic coverage comparison.
- **Plankton biodiversity and species co-occurrence based on environmental DNA – a multiple marker study.** ScienceDirect. **[check]** Multiple-marker plankton design; useful for discussing marker complementarity.
- **From fish to invertebrates: multi-marker eDNA metabarcoding for monitoring wetland biodiversity and non-indigenous species, Macao SAR.** Scientific Reports, 2026. DOI 10.1038/s41598-026-39652-8. **[check]** A recent wetland multi-marker monitoring paper — good for positioning yours as a wetland-monitoring contribution.

### C. Linking community to water quality, and disturbed vs reference sites (Discussion)

This is where your pH/DO/BOD/COD/nutrient measurements earn their place, and where the Deepor-as-pressured / Chandubi-as-reference framing lives.

- **Environmental DNA metabarcoding revealed the impacts of anthropogenic activities on phytoplankton diversity in Dianchi Lake and its three inflow rivers.** 2023. PubMed 37214604 / PMC10196938. **[check]** The key analogue for your core narrative: eutrophic, human-pressured water body read through eDNA phytoplankton, related to nutrient/anthropogenic variables. Model your Deepor discussion on how they connect indicator taxa to pressure.
- **Assessment of planktonic community diversity and stability in lakes and reservoirs based on eDNA metabarcoding — Minghu National Wetland Park, China.** Environmental Research (ScienceDirect S0013935125002762). **[check]** Wetland-park plankton eDNA comparing water bodies — close to your two-wetland comparison in spirit.
- Your indicator-species hook: *Keratella tropica* and *Brachionus caudatus* are established eutrophy indicators, and both are enriched at Deepor. That is the cleanest quantitative link you can draw between the COI data and Deepor's known nutrient loading — stated as *consistent with*, not *proof of*, eutrophication, given n = 1.

### D. The unassigned-ASV / reference-database gap (Methods + Discussion, and a real result)

- A short methods note and a review on freshwater invertebrate primer/reference limitations will support the point that missing copepods/cladocerans reflect reference-database gaps for Indian freshwater fauna, not true absence. **Advancing aquatic biodiversity assessments of invertebrates using eDNA metabarcoding: a systematic evaluation of primers (Chen, Methods in Ecology and Evolution, 2025)** is a candidate here. **[check]** Recovering those taxa by BLASTing unassigned ASVs against NCBI nt and BOLD would convert a limitation into a findings paragraph.

### E. Chloroplast 16S / phytoplankton marker (for when the third dataset arrives)

- **Comparison of Metabarcoding and Shotgun Sequencing Confirms the Relevance of Chloroplastic rRNA Genes to Assess Community Structure of Lake Phytoplankton.** Lemonnier, Molecular Ecology Resources, 2026. DOI 10.1111/1755-0998.70077. **[check — page blocked me, confirm directly]** The justification paper for your chloroplast 16S marker; hold it for the phytoplankton section once that run is delivered.

### F. Regional baseline — Deepor Beel and Assam wetlands (Introduction + your between-study comparison)

These are morphology-based surveys, not metabarcoding. Their value is twofold: they describe your study sites with citable authority, and they give you a microscopy species list to compare your molecular list against — which, per the PeerJ paper's approach, is often the most interesting part of a metabarcoding write-up.

- **Zooplankton communities of Deepor Beel (a Ramsar site), Assam (NE India): ecology, richness, and abundance.** Tropical Ecology 52(3):293–302, 2011. **[check citation]**
- **Phytoplankton diversity of Deepor beel — a Ramsar site and floodplain lake of the Brahmaputra basin.** Indian Journal of Fisheries 62(1):33–40, 2015. **[check citation]**
- **Algal Diversity in Deepor Beel of Assam: A Ramsar Site of North East India.** Nelumbo (BSI), 2021. **[check citation]**
- **Biodiversity of Deepor Beel Ramsar site of Assam (Faunal Diversity).** **[check citation]**
- For Chandubi Beel the published record is thinner — worth a dedicated search; if little exists, that strengthens your novelty claim for the reference site.

### G. Indian freshwater eDNA context (Introduction framing)

- **Environmental DNA (eDNA): an eco-friendly approach for conservation of Indian freshwater diversity — a review.** Environmental Science and Pollution Research, 2025. DOI 10.1007/s11356-025-36202-z. **[check]** Lets you situate your work in the still-small body of Indian freshwater eDNA studies and argue the NE India wetland gap.

---

## 3. A manuscript structure that fits this data

**Framing:** *A multi-marker eDNA metabarcoding baseline of plankton diversity in two contrasting Brahmaputra-valley wetlands — the Ramsar, anthropogenically pressured Deepor Beel and the relatively undisturbed Chandubi Beel.* Descriptive, honest about n = 1, strong on the multi-marker angle and the regional novelty.

- **Introduction.** Wetland plankton as bioindicators → limits of microscopy for small/soft-bodied plankton → eDNA metabarcoding and why multiple markers (group B) → the thin Indian/NE-India record (group G) → Deepor's Ramsar status and pressures vs Chandubi as reference (group F) → aim: a multi-marker baseline and a first molecular comparison.
- **Methods.** Sites and water-quality sampling; DNA/eDNA extraction; the three markers and their primers (COI confirmed as mlCOIintF/HCO2198; 18S V4; chloroplast 16S when delivered); Illumina MiSeq 2×300; QIIME 2 / DADA2 ASVs; reference databases and classifier (request exact details from Eurofins); diversity indices and ordination computed in R (vegan/phyloseq). State plainly that n = 1 per site precludes inferential testing.
- **Results.** Sequencing effort and rarefaction (depth was sufficient — a clean statement); COI zooplankton composition and diversity; 18S micro-eukaryote/phytoplankton composition; the between-lake contrast per marker; the unassigned fraction and what BLAST recovers; indicator taxa (*Keratella*, *Brachionus*).
- **Discussion.** The Deepor-vs-Chandubi pattern against known water-quality differences (group C), framed as consistent-with; marker complementarity — what COI saw that 18S didn't and vice versa (group A, B); the reference-database gap for Indian freshwater crustaceans (group D); comparison to the historical microscopy records (group F); limitations (n = 1, read-count ≠ abundance, separate denoising, no controls); value as a baseline.
- **Conclusion.** First multi-marker molecular plankton inventory of these two wetlands; a reusable baseline; the case for seasonal/replicated follow-up (your PhD direction).

**Target journals** worth checking against scope: *Environmental Monitoring and Assessment*, *Biodiversity Data Journal* (explicitly welcomes inventories), *Journal of Asia-Pacific Biodiversity*, *Tropical Ecology*, *Limnology*.

---

## 4. The three things that most raise this paper's ceiling

1. **BLAST the abundant unassigned COI ASVs** against NCBI nt and BOLD — this is where your missing copepods and cladocerans are, and recovering them is a genuine result, not just a fix. Needs the representative sequences (FASTA / rep-seqs.qza) from Eurofins.
2. **More samples, if at all possible.** Even a few field replicates or one more season per lake unlocks the entire inferential toolkit (PERMANOVA, NMDS, indicator-species analysis) that groups A and C rely on and shifts the paper from baseline to comparison.
3. **Paired microscopy counts**, if you have them from the same samples — the molecular-vs-morphology comparison is frequently the most-cited part of such papers.

---

## 5. Verification status

Directly confirmed against the source: PeerJ 10.7717/peerj.11057 (design; author list still to confirm) and Environmental Management 10.1007/s00267-025-02357-1 (corrected my initial assumption — it's South Korea, not India). All items marked **[check]** come from search-result metadata; several publisher and NCBI pages blocked automated access today, so resolve each DOI yourself before it goes into a reference list. The regional Deepor Beel citations are from ResearchGate listings — confirm volume/page details against the journals.
