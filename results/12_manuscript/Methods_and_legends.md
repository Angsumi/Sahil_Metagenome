# Methods (bioinformatics) — draft

*Generated from the pipeline in this repository (`scripts/`). Sampling, DNA extraction and PCR details must be added by the authors from the sequencing provider's report (marked **[TO ADD]**).*

## Sampling and sequencing

Surface water was collected from Chandubi Beel (W1) and Deepor Beel (W2), Assam, India **[TO ADD: date, coordinates, volume filtered, filter type, preservation]**. DNA was extracted **[TO ADD: kit]** and two markers were amplified by Eurofins Genomics (order GS_2026_NGS-173): the V4 region of the 18S rRNA gene with primers E572F (5′-CYGCGGTAATTCCAGCTC-3′) and E1009R (5′-AYGGTATCTRWTCRTCTTYG-3′) (Comeau et al. 2011), and the ~313 bp "Leray" fragment of the mitochondrial COI gene with primers mlCOIintF (5′-GGWACWGGWTGAACWGTWTAYCCYCC-3′) (Leray et al. 2013) and jgHCO2198 (5′-TAIACYTCIGGRTGICCRAARAAYCA-3′) (Geller et al. 2013) **[TO ADD: PCR conditions, cycles]**. Libraries were sequenced on an Illumina MiSeq (2 × 300 bp; run M04635:72:000000000-MDYKK). The primer pairs were confirmed directly from the reads.

## Read processing

Raw read integrity was checked against the provider's MD5 checksums, and quality was assessed with FastQC v0.13.0 and MultiQC v1.35. Primers were removed with Cutadapt v5.2 using linked adapters: the 5′ primer was required at the start of each read (maximum error rate 0.15), the reverse-complemented opposite primer was trimmed if present, and read pairs lacking either primer were discarded (87.8–89.6 % of pairs retained).

Reads were processed in R v4.5.3 with DADA2 v1.38.0 (Callahan et al. 2016) separately for each marker. Reads were truncated to 270/210 bp (18S, forward/reverse) and 250/200 bp (COI) and filtered with maxEE = 2/4, maxN = 0 and truncQ = 2. Error models were learned per read direction, and both samples were denoised jointly (`pool = TRUE`) so that identical sequences received the same amplicon sequence variant (ASV) in both lakes. Read pairs were merged (minimum overlap 12 bp, no mismatches) and chimeras removed with the consensus method. ASVs were then curated: COI ASVs were retained only if their length differed from 313 bp by whole codons (± 30 bp) and they translated without stop codons in the coding frame (+2) under the invertebrate mitochondrial genetic code (NCBI table 5); 18S ASVs were retained if 350–480 bp. Overall, 53–57 % (18S) and 70–72 % (COI) of raw read pairs were retained in the final tables (982 18S and 345 COI ASVs; Table 1).

## Taxonomic assignment

ASVs were classified with the SINTAX algorithm in VSEARCH v2.32.0 (Rognes et al. 2016; Edgar 2016) against PR2 v5.1.1 (18S; Guillou et al. 2013) and the Eukaryote CO1 Reference Set v5.1.0 (COI; Porter & Hajibabaei 2018). The closest reference sequence of each ASV was found by global alignment in VSEARCH. A rank was accepted only if the SINTAX bootstrap support was ≥ 0.80 and the identity to the closest reference reached a rank-specific minimum (COI: order 85 %, family 90 %, genus 95 %, species 97 %; 18S: family 95 %, genus 97 %, species 99 %). Ranks were accepted top-down; PR2 placeholder names were left blank without blocking lower ranks.

The 40 most abundant COI ASVs with < 85 % identity to the reference set were searched against NCBI core_nt with BLASTn (megablast; blastn with word size 11 for queries without hits; E ≤ 1e-20) through the NCBI BLAST URL API, and their lineages retrieved from NCBI Taxonomy. Hits < 80 % identity were not used for classification. ASVs among these without a ≥ 90 % DNA match were further compared at the protein level: the Eukaryote CO1 Reference Set was translated (invertebrate mitochondrial code, the reading frame with fewest stop codons per sequence) with SeqKit v2.14.0, and the ASVs were searched against it with DIAMOND v2.2.8 blastx (`--ultra-sensitive`, query genetic code 5, E ≤ 1e-10; Buchfink et al. 2021). A consensus phylum and class was assigned when at least three hits lay within 95 % of the best bit score and ≥ 70 % of them agreed; hits with undefined phylum in the reference were labelled by class.

## Diversity and community analyses

Analyses used vegan v2.7.5 (Oksanen et al.). Alpha diversity was computed after rarefying both lakes to the shallower depth of each marker (18S: 81,828; COI: 102,761 reads), averaged over 100 random subsamples, and reported as observed ASVs, Shannon, Simpson and Pielou's evenness, and Hill numbers q1 = exp(H′) and q2 = 1/D. Chao1 was not computed because DADA2 removes singletons. Overlap between lakes was summarised at ASV, genus and species level (shared/unique counts, Jaccard similarity, Bray–Curtis dissimilarity on relative abundances). With one sample per lake, no inferential statistics were performed.

18S ASVs were grouped into ecological roles from their PR2 division and class (green algae, desmids, diatoms, other algae, dinoflagellates, free-living protozoa, parasitic protists, fungi, oomycetes, animals). COI ASVs were grouped by animal group using the reference-set phylum or, for the BLAST-searched ASVs, the NCBI phylum of hits ≥ 80 % identity. For the rotifer trophic quotient QB/T (Sládeček 1983), COI ASVs were clustered into species-level MOTUs at 97 % identity with VSEARCH (`--cluster_size`), and Brachionus and Trichocerca MOTUs counted per lake; genus labels from BLAST hits of 80–90 % identity were treated as provisional.

## Data availability

Raw reads: NCBI SRA **[TO ADD: BioProject accession]**. ASV sequences, tables, taxonomy and all scripts: https://github.com/Angsumi/Sahil_Metagenome (archive with a DOI before submission).

---

# Figure legends

**Figure 1.** Read processing and sequencing depth. (A) Read pairs remaining after each processing step for each marker and lake. (B) Rarefaction curves of curated ASVs; flattening curves indicate sufficient sequencing depth.

**Figure 2.** Community composition. (A) Share of 18S rRNA reads by ecological role. (B) Share of COI reads by animal group, combining reference-set assignments and NCBI BLAST look-ups (≥ 80 % identity).

**Figure 3.** Diversity and overlap. (A) Alpha diversity as effective numbers of ASVs (richness, Hill q1, Hill q2) after rarefaction to equal depth. (B) Share of ASVs, named genera and named species found only in Chandubi Beel, in both lakes, or only in Deepor Beel; numbers are counts.

**Figure 4.** The 30 most abundant named genera from both markers, as percentage of all reads of the respective marker in each lake, ordered from Chandubi-leaning to Deepor-leaning.

**Figure 5.** Unknown COI ASVs: identity to the closest known sequence at DNA level (GenBank, BLASTn) and protein level (translated CO1 Reference Set, DIAMOND), labelled with the consensus phylum/class of the closest proteins.

**Figure 6.** Rotifer genera represented by species-level MOTUs (COI, 97 % clusters) in each lake, with the Brachionus:Trichocerca quotient (QB/T).

# References to verify before citing

Callahan et al. 2016 (DADA2) · Comeau et al. 2011 (E572F/E1009R) · Edgar 2016 (SINTAX) · Geller et al. 2013 (jgHCO2198) · Guillou et al. 2013 (PR2) · Leray et al. 2013 (mlCOIintF) · Oksanen et al. (vegan) · Porter & Hajibabaei 2018 (CO1 classifier) · Rognes et al. 2016 (VSEARCH) · Buchfink et al. 2021 (DIAMOND) · Shen et al. 2016 (SeqKit) · Sládeček 1983 (QB/T) · Martin 2011 (Cutadapt) · Ewels et al. 2016 (MultiQC).
