// Step 16 — Build the manuscript as a Word file formatted for Environmental Monitoring and Assessment
// (Springer): 10-pt Times, continuous line numbers, automatic page numbers, unnumbered headings
// (level 1 bold, level 2 normal), figures embedded with "Fig." captions, Word tables, APA references.
// Numbers are read from results/; references from the Crossref records of step 14.
// Markup in text: *italic*, [[Key1;Key2]] = parenthetical citation, [[@Key]] = narrative citation.
// Run: NODE_PATH=work/node/node_modules node scripts/16_manuscript_docx.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType,
  Footer, PageNumber, LineNumberRestartFormat, BorderStyle, ShadingType, HeadingLevel,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const R = (p) => path.join(ROOT, p);
const tsv = (p) => {
  const [h, ...rows] = fs.readFileSync(R(p), "utf8").trim().split("\n").map((l) => l.split("\t"));
  return rows.map((r) => Object.fromEntries(h.map((k, i) => [k, r[i]])));
};
const num = (x, d = 1) => Number(x).toFixed(d);
const int = (x) => Math.round(Number(x)).toLocaleString("en-US");

// ---------------------------------------------------------------- data
const track = Object.fromEntries(tsv("results/05_summary/read_tracking.tsv").map((r) => [`${r.marker}_${r.sample}`, r]));
const alpha = Object.fromEntries(tsv("results/08_diversity/alpha_diversity.tsv").map((r) => [`${r.marker}_${r.sample}`, r]));
const ovl = Object.fromEntries(tsv("results/08_diversity/overlap_by_level.tsv").map((r) => [`${r.marker}_${r.level}`, r]));
const roles = Object.fromEntries(tsv("results/09_ecology/18S_ecological_roles.tsv").map((r) => [r.role, r]));
const cgrp = Object.fromEntries(tsv("results/09_ecology/COI_animal_groups.tsv").map((r) => [r.group, r]));
const qbt = Object.fromEntries(tsv("results/11_rotifer_index/QBT_index.tsv").map((r) => [r.sample, r]));
const tsum = Object.fromEntries(tsv("results/06_taxonomy/taxonomy_summary.tsv").map((r) => [r.marker, r]));
const depth = Object.fromEntries(tsv("results/06_taxonomy/assignment_depth.tsv").map((r) => [`${r.marker}_${r.rank}`, r]));
const prot = tsv("results/10_protein/COI_protein_summary.tsv");
const protRot = tsv("results/10_protein/COI_protein_by_group.tsv").find((r) => r.consensus_phylum === "Rotifera");
const top = tsv("results/06_taxonomy/COI_blast_unknowns_summary.tsv").find((r) => r.asv === "COI_ASV0001");
const topProt = prot.find((r) => r.asv === "COI_ASV0001");
const micro = tsv("results/15_microscopy/comparison_summary.tsv");
const alg = tsv("results/15_microscopy/algae_genera_microscopy_vs_DNA.tsv");
const animalMark = tsv("results/09_ecology/animal_genera_by_marker.tsv");
const ind = tsv("results/09_ecology/indicator_taxa.tsv");
const dada = { "18S": JSON.parse(fs.readFileSync(R("results/03_dada2/18S/summary.json"))),
               COI: JSON.parse(fs.readFileSync(R("results/03_dada2/COI/summary.json"))) };
const cur = tsv("results/04_curation/curation_summary.tsv");
const refs = JSON.parse(fs.readFileSync(R("results/14_references/references_records.json")));

const rawTotal = Object.values(track).reduce((a, r) => a + Number(r.raw), 0);
const algae = (s) => ["Green algae", "Desmids & conjugating algae", "Diatoms", "Golden & other algae", "Dinoflagellates"]
  .reduce((a, k) => a + Number(roles[k][s]), 0);
const curRemoved = (m) => {
  const rows = cur.filter((r) => r.marker === m);
  const kept = rows.find((r) => r.reason === "kept");
  const rem = rows.filter((r) => r.reason !== "kept");
  const remReads = rem.reduce((a, r) => a + Number(r.W1_reads) + Number(r.W2_reads), 0);
  const all = remReads + Number(kept.W1_reads) + Number(kept.W2_reads);
  return { asvs: rem.reduce((a, r) => a + Number(r.asvs), 0), pct: (100 * remReads) / all };
};
const indv = (name) => ind.find((r) => r.name === name);
const mic = (label) => micro.find((r) => r.comparison.startsWith(label));
const algBoth = alg.filter((r) => r.found_by === "both").length;
const algDnaOnly = alg.filter((r) => r.found_by === "DNA only").length;
const algBlind = alg.filter((r) => r.found_by === "microscopy only" && r.note).length;
const nBy = (k) => animalMark.filter((r) => r.detected_by === k).length;
const protRotN = Number(protRot.asvs);

// ---------------------------------------------------------------- citations
const refName = (k) => {
  const r = refs[k];
  if (!r) throw new Error(`unknown reference ${k}`);
  const a = r.authors.map((x) => x.family);
  const who = a.length === 1 ? a[0] : a.length === 2 ? `${a[0]} & ${a[1]}` : `${a[0]} et al.`;
  return { who, year: r.year };
};
const EXTRA = { Oksanen: { who: "Oksanen et al.", year: 2025 }, RCore: { who: "R Core Team", year: 2026 } };
const citeOne = (k) => EXTRA[k] || refName(k);
function expand(text) {
  return text.replace(/\[\[(@?)([^\]]+)\]\]/g, (_, narrative, keys) => {
    const items = keys.split(";").map((k) => citeOne(k.trim()));
    if (narrative) return items.map((c) => `${c.who} (${c.year})`).join("; ");
    return "(" + items.map((c) => `${c.who}, ${c.year}`).join("; ") + ")";
  });
}

// ---------------------------------------------------------------- paragraph helpers
const FONT = "Times New Roman";
const SIZE = 20; // half-points: 10 pt
function runs(text, base = {}) {
  const out = [];
  expand(text).split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).forEach((seg) => {
    if (!seg) return;
    if (seg.startsWith("**")) out.push(new TextRun({ text: seg.slice(2, -2), bold: true, font: FONT, size: SIZE, ...base }));
    else if (seg.startsWith("*")) out.push(new TextRun({ text: seg.slice(1, -1), italics: true, font: FONT, size: SIZE, ...base }));
    else out.push(new TextRun({ text: seg, font: FONT, size: SIZE, ...base }));
  });
  return out;
}
const P = (text, opts = {}) => new Paragraph({ children: runs(text), spacing: { after: 120, line: 360 },
  alignment: AlignmentType.JUSTIFIED, ...opts });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, bold: true, font: FONT, size: 22 })],
  spacing: { before: 240, after: 240 } });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT, size: SIZE, italics: true })],
  spacing: { before: 200, after: 200 } });

const figs = [];
function FIG(n, caption) {
  const file = R(`results/12_manuscript/figures/Fig${n}.png`);
  const buf = fs.readFileSync(file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const width = 640; // ~6.7 in at 96 px/in, within the 174-mm column
  figs.push(n);
  return [
    new Paragraph({ children: [new ImageRun({ type: "png", data: buf, transformation: { width, height: Math.round((width * h) / w) },
      altText: { title: `Fig. ${n}`, description: caption.replace(/\*/g, ""), name: `Fig${n}` } })],
      alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 } }),
    new Paragraph({ children: [new TextRun({ text: `Fig. ${n} `, bold: true, font: FONT, size: SIZE }), ...runs(caption)],
      spacing: { after: 240, line: 300 } }),
  ];
}

const BORDER = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const NONE = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
function TABLE(n, caption, header, rows, widths, note) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, isHead, last) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA },
    borders: { top: isHead ? BORDER : NONE, bottom: isHead || last ? BORDER : NONE, left: NONE, right: NONE },
    children: [new Paragraph({ children: runs(String(t), { size: 18, bold: isHead }),
      alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.RIGHT })],
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
  });
  const out = [
    new Paragraph({ children: [new TextRun({ text: `Table ${n} `, bold: true, font: FONT, size: SIZE }), ...runs(caption)],
      spacing: { before: 240, after: 80, line: 300 } }),
    new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
      rows: [new TableRow({ tableHeader: true, children: header.map((t, i) => cell(t, i, true, false)) }),
             ...rows.map((r, j) => new TableRow({ children: r.map((t, i) => cell(t, i, false, j === rows.length - 1)) }))] }),
  ];
  if (note) out.push(new Paragraph({ children: runs(note, { size: 16 }), spacing: { before: 60, after: 240 } }));
  return out;
}

// ---------------------------------------------------------------- content
const C = "Chandubi Beel", D = "Deepor Beel";
const a = (m, s, k, d = 1) => num(alpha[`${m}_${s}`][k], d);
const t = (m, s) => track[`${m}_${s}`];

const TITLE = "Multi-marker eDNA metabarcoding reveals contrasting micro-eukaryote communities and a shared rotifer assemblage in two Brahmaputra floodplain wetlands of Assam, India";

const abstract = `Floodplain wetlands of the Brahmaputra valley are under growing urban pressure, yet molecular baselines of their plankton are lacking. We characterised the plankton of Deepor Beel, a Ramsar wetland bordering the municipal solid-waste dumping ground of Guwahati, and the less disturbed Chandubi Beel using environmental DNA metabarcoding of two markers: the 18S rRNA V4 region for micro-eukaryotes and the mitochondrial cytochrome c oxidase I (COI) gene for metazoans. From ${int(rawTotal)} read pairs, joint denoising yielded ${int(tsum["18S"].asvs)} 18S and ${int(tsum.COI.asvs)} COI amplicon sequence variants. The micro-eukaryote communities were almost distinct (${ovl["18S_ASV"].pct_shared}% of variants shared): Chandubi Beel was dominated by green algae, diatoms and free-living protozoa, whereas Deepor Beel was richer (${int(alpha["18S_W2"].observed)} vs ${int(alpha["18S_W1"].observed)} variants) and dominated by fungi (${num(roles.Fungi.W2, 0)}% of reads), oomycetes and desmids. In contrast, ${ovl["COI_ASV"].pct_shared}% of COI variants occurred in both wetlands, where rotifers formed ${num(cgrp.Rotifers.W1, 0)}–${num(cgrp.Rotifers.W2, 0)}% of reads. Protein-level searches placed ${protRotN} of the abundant unassigned COI variants among rotifers, revealing many rotifer lineages absent from reference libraries. The rotifer quotient QB/T of ${qbt.W1.QBT} in both wetlands and the enrichment of *Brachionus* and *Keratella tropica* at Deepor Beel indicate nutrient-rich conditions. DNA detections agreed with published microscopy for the dominant desmid and rotifer genera. These results provide the first molecular plankton baseline for both wetlands and show that combining markers is essential for wetland biomonitoring in north-eastern India.`;

const keywords = "Biomonitoring · Ramsar site · Zooplankton · Phytoplankton · Desmids · Cytochrome c oxidase I";

const intro = [
  `Wetland plankton respond within weeks to changes in nutrient load, organic matter and hydrology, which makes them sensitive indicators of ecological condition. Identifying them by microscopy is, however, slow and demands separate expertise for rotifers, crustaceans, protists and algae, while small and fragile forms are routinely overlooked. Environmental DNA (eDNA) metabarcoding offers a complementary route: DNA shed into the water is amplified with taxonomically informative markers and sequenced in a single assay, and its use for monitoring Indian fresh waters is growing [[Sahu2025]].`,
  `No single marker recovers a whole plankton community. Mitochondrial cytochrome c oxidase I (COI) resolves metazoan zooplankton to species where reference sequences exist, whereas the nuclear 18S rRNA gene captures the broader eukaryotic assemblage — algae, protists and fungi — usually at coarser taxonomic ranks. Studies that combine markers consistently detect more taxa than either marker alone [[Zhang2018;Stefanni2018;Sildever2021;Zhao2021]], and eDNA surveys have linked shifts in plankton composition to anthropogenic pressure in lakes and reservoirs [[Lin2023;Jo2026]]. The reliability of species-level assignments nevertheless depends on reference databases, which remain incomplete for tropical freshwater invertebrates [[Chen2025]].`,
  `Deepor Beel is a Ramsar-listed floodplain wetland of the Brahmaputra on the south-western edge of Guwahati, the largest city of north-eastern India. It lies immediately beside the city's municipal solid-waste dumping ground, which exposes it to leachate and organic enrichment in addition to urban encroachment. Chandubi Beel, a natural lake in the same district, is comparatively undisturbed. The rotifers and algae of Deepor Beel have been described by microscopy [[Sharma2010;Baruah2020]], but no molecular survey exists for either wetland.`,
  `Here we provide a multi-marker eDNA baseline for the plankton of both wetlands. We asked (i) how the micro-eukaryote and metazoan communities of the pressured and the reference wetland differ, (ii) what biological indicators reveal about their trophic state in the absence of chemical monitoring, (iii) how much of the community can be named with current reference libraries, and (iv) whether DNA detections agree with earlier microscopy.`,
];

const methods = [
  ["Study area and sampling",
   `Surface water was collected at one near-shore location in each wetland: Deepor Beel (W2; [sampling coordinates]) and Chandubi Beel (W1; [sampling coordinates]), Kamrup district, Assam, India. The study was designed as a biological baseline and did not include water chemistry; the contrast between the wetlands is defined by their setting — Deepor Beel adjoining the municipal solid-waste dumping ground of Guwahati and Chandubi Beel without comparable pressure — and the trophic state of each is inferred from biological indicators (see below).`],
  ["DNA extraction, amplification and sequencing",
   `DNA extraction, PCR amplification and library preparation were carried out by Eurofins Genomics following the provider's standard amplicon protocol. Two markers were amplified: the V4 region of the 18S rRNA gene with primers E572F (5′-CYGCGGTAATTCCAGCTC-3′) and E1009R (5′-AYGGTATCTRWTCRTCTTYG-3′) [[Comeau2011]], and the 313-bp "Leray" fragment of COI with mlCOIintF (5′-GGWACWGGWTGAACWGTWTAYCCYCC-3′) [[Leray2013]] and jgHCO2198 (5′-TAIACYTCIGGRTGICCRAARAAYCA-3′) [[Geller2013]]. Libraries were sequenced on an Illumina MiSeq (2 × 300 bp). The identity of both primer pairs was confirmed directly from the reads.`],
  ["Read processing",
   `Read integrity was verified against the provider's MD5 checksums and quality assessed with FastQC v0.13.0 and MultiQC v1.35 [[Ewels2016]]. Primers were removed with Cutadapt v5.2 [[Martin2011]] using linked adapters: the 5′ primer was required at the start of each read (maximum error rate 0.15), the reverse-complemented opposite primer was trimmed when present, and pairs lacking either primer were discarded. Reads were then processed per marker with DADA2 v1.38.0 [[Callahan2016]] in R v4.5.3 [[RCore]]: truncation at ${dada["18S"].truncLen.join("/")} bp (18S) and ${dada.COI.truncLen.join("/")} bp (COI), maxEE 2/4, maxN 0, error models learned per read direction, joint (pooled) denoising of both samples so that identical sequences received the same amplicon sequence variant (ASV) in both wetlands, merging with a minimum overlap of 12 bp and no mismatches, and consensus chimera removal. COI ASVs were retained only if their length differed from 313 bp by whole codons and they translated without stop codons under the invertebrate mitochondrial code (NCBI table 5); 18S ASVs were retained if 350–480 bp long.`],
  ["Taxonomic assignment",
   `ASVs were classified with the SINTAX algorithm [[Edgar2016]] in VSEARCH v2.32.0 [[Rognes2016]] against PR2 v5.1.1 for 18S [[Guillou2013]] and the Eukaryote CO1 Reference Set v5.1.0 for COI [[Porter2018]]. A rank was accepted only if its bootstrap support was ≥ 0.80 and the identity to the closest reference sequence reached a rank-specific minimum (COI: order 85%, family 90%, genus 95%, species 97%; 18S: family 95%, genus 97%, species 99%). The 40 most abundant COI ASVs with < 85% identity to the reference set were searched against NCBI core_nt with BLASTn; hits below 80% identity were not used. ASVs among these without a ≥ 90% DNA match were further compared at the protein level: the reference set was translated with SeqKit v2.14.0 [[Shen2016]] and searched with DIAMOND v2.2.8 blastx [[Buchfink2021]] (ultra-sensitive mode, invertebrate mitochondrial code, E ≤ 10⁻¹⁰). A consensus phylum was assigned when at least three hits lay within 95% of the best bit score and ≥ 70% of them agreed.`],
  ["Community analyses",
   `Diversity analyses used vegan v2.7.5 [[Oksanen]]. Alpha diversity was computed after rarefying both samples of each marker to the shallower depth, averaged over 100 random subsamples, and reported as observed ASVs, Shannon, Simpson and Pielou indices and Hill numbers (q1 = exp H′; q2 = 1/D). Overlap between wetlands was summarised as shared and unique ASVs, genera and species with Jaccard similarity and Bray–Curtis dissimilarity. 18S ASVs were grouped into ecological roles from their PR2 division and class, and COI ASVs into animal groups. For the rotifer quotient QB/T [[Sladecek1983]], COI ASVs were clustered into species-level operational units at 97% identity with VSEARCH and *Brachionus* and *Trichocerca* units counted per wetland. DNA detections for Deepor Beel were compared with the taxa reported by microscopy for rotifers [[Sharma2010]] and algae [[Baruah2020]]. With one sample per wetland, no inferential statistics were applied; all contrasts are descriptive. Bioinformatic scripts and draft text were prepared with the assistance of a large language model (Claude, Anthropic); all code, results and text were checked by the authors. All scripts are publicly available (see Data availability).`],
];

const results = [
  ["Sequencing depth and data processing", [
    `Sequencing produced ${int(rawTotal)} read pairs, of which 87.8–89.6% carried both primers (Table 1). After denoising, merging, chimera removal (${num(dada["18S"].chimeric_read_pct)}% of 18S and ${num(dada.COI.chimeric_read_pct)}% of COI reads) and curation, ${num(t("18S", "W1").pct_retained)}–${num(t("18S", "W2").pct_retained)}% (18S) and ${num(t("COI", "W1").pct_retained)}–${num(t("COI", "W2").pct_retained)}% (COI) of raw pairs were retained. Curation removed few reads (COI: ${curRemoved("COI").asvs} ASVs, ${num(curRemoved("COI").pct)}% of reads; 18S: ${curRemoved("18S").asvs} ASVs, ${num(curRemoved("18S").pct)}%), and the retained COI ASVs clustered at 313 and 316 bp, as expected for a protein-coding fragment. Rarefaction curves reached a plateau for both markers in both wetlands (Fig. 1), indicating that sequencing depth was sufficient.`,
  ]],
  ["Taxonomic resolution and the reference-library gap", [
    `The 18S data were well covered by PR2: ${num(depth["18S_Division"].W1, 0)}–${num(depth["18S_Division"].W2, 0)}% of reads were named at division level and ${tsum["18S"].named_genera} genera were identified. COI resolution was much lower: only ${num(depth.COI_Phylum.W1, 0)}% (${C}) and ${num(depth.COI_Phylum.W2, 0)}% (${D}) of reads were named even to phylum, because ${num(tsum.COI.reads_below_85pct_identity, 0)}% of COI reads were less than 85% identical to any reference sequence. GenBank searches showed that many of these unknowns matched unnamed "rotifer environmental samples" or known rotifers at only 80–89% DNA identity. At the protein level, ${protRotN} of ${prot.length} such ASVs were placed among rotifers with 89–98% amino-acid identity to *Trichocerca*, *Euchlanis*, *Filinia*, *Lecane* and *Brachionus* (Fig. 2), together accounting for ${num(protRot.W1_pct, 0)}% and ${num(protRot.W2_pct, 0)}% of COI reads. The single most abundant COI variant (${num(top.reads_pct_W1, 0)}–${num(top.reads_pct_W2, 0)}% of reads in both wetlands) translated cleanly but was at most ${num(top.ncbi_identity, 0)}% identical to any GenBank sequence, and its protein fell between a nematode (${num(topProt.aa_identity, 0)}%) and stramenopile algae, so its identity remains unresolved. These results show that the gap lies in the reference libraries rather than in the data: north-eastern Indian rotifers are poorly represented, consistent with the limitations noted for freshwater invertebrates generally [[Chen2025]].`,
  ]],
  ["Community composition and ecological roles", [
    `The micro-eukaryote communities of the two wetlands differed in structure (Fig. 3a). In ${C}, algae formed ${num(algae("W1"), 0)}% of 18S reads, dominated by green algae (${num(roles["Green algae"].W1, 0)}%; *Desmodesmus*, *Chlamydomonas*, *Pteromonas*) and diatoms (${num(roles.Diatoms.W1, 0)}%; *Cyclotella*, *Aulacoseira*, *Nitzschia*), together with free-living protozoa (${num(roles["Protozoa (free-living)"].W1, 0)}%), notably the cercozoan *Neoheteromita*. In ${D}, algae formed a similar share (${num(algae("W2"), 0)}%) but were dominated by desmids (${num(roles["Desmids & conjugating algae"].W2, 0)}%; *Staurastrum*, *Cosmarium*, *Pleurotaenium*), and fungi (${num(roles.Fungi.W2, 0)}%) and oomycetes (${num(roles["Water moulds (oomycetes)"].W2, 0)}%) took a far larger share than in ${C} (${num(roles.Fungi.W1, 0)}% and ${num(roles["Water moulds (oomycetes)"].W1, 0)}%). The most abundant Deepor-specific genera were the oomycete *Aphanomyces*, the algal-parasitic chytrid *Rhizophydium* and the golden alga *Lepidochromonas* (Fig. 4). A micro-eukaryote community weighted towards decomposers and parasites is consistent with the organic input expected beside a solid-waste dumping ground.`,
    `In the COI data, rotifers dominated both wetlands (${num(cgrp.Rotifers.W1, 0)}% and ${num(cgrp.Rotifers.W2, 0)}% of reads after integrating reference and protein-level assignments; Fig. 3b), led by *Brachionus* and *Keratella*. Copepods, ostracods and insects together contributed less than 1% of COI reads, although copepods (*Mesocyclops*, *Microcyclops* and *Eucyclops*) were recovered by 18S.`,
  ]],
  ["Diversity and overlap between wetlands", [
    `The two markers gave opposite diversity rankings (Table 2, Fig. 5a). For 18S, ${D} was considerably richer (${int(alpha["18S_W2"].observed)} vs ${int(alpha["18S_W1"].observed)} ASVs at equal depth; Hill q1 ${a("18S", "W2", "hill_q1")} vs ${a("18S", "W1", "hill_q1")}). For COI, ${C} was richer and more even (${int(alpha.COI_W1.observed)} vs ${int(alpha.COI_W2.observed)} ASVs; q1 ${a("COI", "W1", "hill_q1")} vs ${a("COI", "W2", "hill_q1")}), reflecting the stronger dominance of a few rotifers in ${D}.`,
    `Overlap differed even more (Fig. 5b). Only ${ovl["18S_ASV"].pct_shared}% of 18S ASVs and ${ovl["18S_Genus"].pct_shared}% of named 18S genera occurred in both wetlands (Bray–Curtis dissimilarity ${num(ovl["18S_ASV"].bray_curtis_dissimilarity, 2)}), whereas ${ovl["COI_ASV"].pct_shared}% of COI ASVs were shared at similar relative abundance (Bray–Curtis ${num(ovl["COI_ASV"].bray_curtis_dissimilarity, 2)}). The wetlands therefore share largely the same rotifer assemblage while hosting distinct algal, protist and fungal communities. A shared rotifer pool is plausible for floodplain lakes of the same river system, as rotifers disperse readily through resting eggs and seasonal hydrological connection, whereas micro-eukaryote producers and decomposers respond more directly to local conditions such as organic loading and macrophyte cover.`,
  ]],
  ["Biological indicators of trophic state", [
    `Without chemical data, the trophic condition of the wetlands can be read from indicator taxa (Table 3). The rotifer quotient QB/T was ${qbt.W1.QBT} in both wetlands (${qbt.W1.brachionus_motus} *Brachionus* against ${qbt.W1.trichocerca_motus} *Trichocerca* species-level units; Fig. 6), well above the threshold of 2 for eutrophic water [[Sladecek1983]]; some genus assignments rest on distant matches and the value is therefore provisional. The eutrophy-associated *Brachionus* (${num(indv("Brachionus").chandubi_pct)}% vs ${num(indv("Brachionus").deepor_pct)}% of COI reads), *B. caudatus* (${num(indv("Brachionus_caudatus").chandubi_pct)}% vs ${num(indv("Brachionus_caudatus").deepor_pct)}%) and *Keratella tropica* (${num(indv("Keratella_tropica").chandubi_pct)}% vs ${num(indv("Keratella_tropica").deepor_pct)}%) were more abundant in ${D}, in line with organic enrichment from the adjacent dumping ground. ${C} nevertheless carried diatoms typical of enriched water — *Cyclotella meneghiniana* (${num(indv("Cyclotella_meneghiniana").chandubi_pct)}%), *Nitzschia palea* and *Aulacoseira granulata* — indicating that it too is nutrient-rich rather than pristine. The prominence of desmids in ${D} reflects its dense macrophyte cover, a habitat in which desmids thrive.`,
  ]],
  ["Agreement with microscopy", [
    `DNA detections for ${D} agreed well with earlier microscopy (Fig. 7). For algae, ${algBoth} of the ${mic("Algal").microscopy} genera listed by [[@Baruah2020]] were also found by 18S, including the dominant desmids *Cosmarium* and *Staurastrum*, and DNA added ${algDnaOnly} genera not listed. Of the genera found only by microscopy, ${algBlind} were cyanobacteria, which lack an 18S gene, or euglenoids, which are poorly amplified by V4 primers. For rotifers, DNA detected ${Number(mic("Rotifer genus").also_by_DNA_named) + Number(mic("Rotifer genus").also_by_DNA_provisional)} of the five quantitatively important genera and ${Number(mic("Rotifer family").also_by_DNA_named) + Number(mic("Rotifer family").also_by_DNA_provisional)} of the seven important families reported by [[@Sharma2010]], but only ${mic("Rotifer species").also_by_DNA_named} of the seven important species, again reflecting the reference-library gap rather than absence.`,
  ]],
  ["Complementarity of markers and limitations", [
    `Of the animal genera named, ${nBy("18S only")} were detected only by 18S (flatworms, gastrotrichs, oligochaetes and the copepods *Eucyclops* and *Microcyclops*), ${nBy("COI only")} only by COI (including *Brachionus*, *Keratella* and *Polyarthra*) and ${nBy("both")} by both. Neither marker alone would have described these wetlands adequately, supporting multi-marker designs for wetland monitoring [[Zhang2018;Stefanni2018;Zhao2021]]. Adding a phytoplankton-specific marker such as chloroplast 16S would further resolve the algal and cyanobacterial fraction [[Lemonnier2025]].`,
    `The study is a baseline with one sample per wetland, so differences are descriptive and cannot be tested statistically. Read proportions reflect DNA abundance, which is affected by copy number, body size and primer affinity, rather than biomass. Indicator interpretations are qualitative, and repeated, seasonal sampling with replication would be needed to quantify the effect of the dumping ground on Deepor Beel.`,
  ]],
];

const conclusions = `This first molecular plankton baseline for Deepor Beel and Chandubi Beel shows two wetlands that share their rotifer zooplankton but differ sharply in their micro-eukaryote communities. Deepor Beel, beside the city's solid-waste dumping ground, carries a richer community dominated by fungi, oomycetes, desmids and decomposers, and a stronger signal of eutrophy-associated rotifers, while Chandubi Beel is dominated by green algae, diatoms and protozoa. Rotifer indicators point to nutrient-rich conditions in both wetlands. Many rotifer lineages and the most abundant metazoan sequence lack reference sequences, which identifies barcoding of the regional fauna as a priority. Combining 18S and COI markers, and checking detections against microscopy, provides a practical framework for monitoring these wetlands.`;

const declarations = [
  ["Acknowledgements", "[Acknowledgements]"],
  ["Author contributions", "Sahil Seikh: conceptualisation, sampling, investigation, data analysis, writing – original draft. [Add other authors and contributions.]"],
  ["Funding", "[State funding sources, or: The authors did not receive support from any organization for the submitted work.]"],
  ["Data availability", "Raw sequence reads are deposited in the NCBI Sequence Read Archive under BioProject [accession]. ASV sequences, ASV and taxonomy tables, and all analysis scripts are available at https://github.com/Angsumi/Sahil_Metagenome."],
  ["Declarations", "Ethics approval: Not applicable; the study used environmental water samples and involved no human participants or animals. Consent to participate: Not applicable. Consent for publication: Not applicable. Competing interests: [The authors declare no competing interests.]"],
];

// ---------------------------------------------------------------- tables
const table1Rows = [];
for (const m of ["18S", "COI"]) for (const s of ["W1", "W2"]) {
  const r = t(m, s);
  table1Rows.push([`${m} — ${s === "W1" ? C : D}`, int(r.raw), int(r.primers_found), int(r.filtered), int(r.merged),
    int(r.nonchim), int(r.curated), num(r.pct_retained)]);
}
const table2Rows = [];
for (const m of ["18S", "COI"]) for (const s of ["W1", "W2"]) {
  const r = alpha[`${m}_${s}`];
  table2Rows.push([`${m} — ${s === "W1" ? C : D}`, int(r.rarefied_to), int(r.observed), num(r.shannon, 2), num(r.simpson, 3),
    num(r.pielou, 2), num(r.hill_q1), num(r.hill_q2)]);
}
const table3Rows = ind.map((r) => [`*${r.name.replace(/_/g, " ")}*`, r.marker, r.group, num(r.chandubi_pct, 2), num(r.deepor_pct, 2)]);

// ---------------------------------------------------------------- references (APA 7)
function apaAuthors(list) {
  const f = (x) => {
    const init = (x.given || "").split(/[\s.\-]+/).filter(Boolean).map((p) => p[0].toUpperCase() + ".").join(" ");
    return init ? `${x.family}, ${init}` : x.family;
  };
  const n = list.map(f);
  if (n.length === 1) return n[0];
  if (n.length <= 20) return n.slice(0, -1).join(", ") + ", & " + n[n.length - 1];
  return n.slice(0, 19).join(", ") + ", … " + n[n.length - 1];
}
const sentence = (s) => s.replace(/\b([A-Z])([a-z]+)\b/g, (w, a1, rest, off) => (off === 0 ? w : w.toLowerCase()))
  .replace(/\b(dna|edna|rrna|pcr|coi|its|illumina|dada2|pr2|vsearch|diamond|seqkit|multiqc|sintax|ramsar|indian|india|assam|north|east|deepor|beel|arctic|ocean|dianchi|lake|singal|reservoir|cutadapt|fasta\/q|cytochrome|co1)\b/gi,
    (w) => ({ dna: "DNA", edna: "eDNA", rrna: "rRNA", pcr: "PCR", coi: "COI", its: "ITS", illumina: "Illumina",
      dada2: "DADA2", pr2: "PR2", vsearch: "VSEARCH", diamond: "DIAMOND", seqkit: "SeqKit", multiqc: "MultiQC",
      sintax: "SINTAX", ramsar: "Ramsar", indian: "Indian", india: "India", assam: "Assam", north: "North", east: "East",
      deepor: "Deepor", beel: "Beel", arctic: "Arctic", ocean: "Ocean", dianchi: "Dianchi", lake: "Lake",
      singal: "Singal", reservoir: "Reservoir", cutadapt: "Cutadapt", "fasta/q": "FASTA/Q", cytochrome: "cytochrome",
      co1: "CO1" })[w.toLowerCase()] || w);
const apaRefs = Object.entries(refs).filter(([k]) => !k.startsWith("Deepor_") || k === "Deepor_algae2021");
// The regional algae paper is keyed Deepor_algae2021 in step 14; cite it as Baruah2020
refs.Baruah2020 = refs.Deepor_algae2021;
const refParas = apaRefs.map(([k, r]) => {
  const parts = [new TextRun({ text: `${apaAuthors(r.authors)} (${r.year}). ${sentence(r.title)}. `, font: FONT, size: SIZE })];
  parts.push(new TextRun({ text: r.journal + (r.volume ? `, ${r.volume}` : ""), italics: true, font: FONT, size: SIZE }));
  parts.push(new TextRun({ text: `${r.issue ? `(${r.issue})` : ""}${r.pages ? `, ${r.pages.replace("-", "–")}` : ""}. https://doi.org/${r.doi}`, font: FONT, size: SIZE }));
  return { key: r.authors[0].family + r.year, p: new Paragraph({ children: parts, indent: { left: 360, hanging: 360 }, spacing: { after: 100, line: 300 } }) };
});
refParas.push({ key: "Oksanen2025", p: new Paragraph({ children: [
  new TextRun({ text: "Oksanen, J., Simpson, G. L., Blanchet, F. G., Kindt, R., Legendre, P., Minchin, P. R., et al. (2025). ", font: FONT, size: SIZE }),
  new TextRun({ text: "vegan: Community ecology package", italics: true, font: FONT, size: SIZE }),
  new TextRun({ text: " (R package version 2.7-5). https://CRAN.R-project.org/package=vegan", font: FONT, size: SIZE })],
  indent: { left: 360, hanging: 360 }, spacing: { after: 100, line: 300 } }) });
refParas.push({ key: "R Core Team2026", p: new Paragraph({ children: [
  new TextRun({ text: "R Core Team. (2026). ", font: FONT, size: SIZE }),
  new TextRun({ text: "R: A language and environment for statistical computing", italics: true, font: FONT, size: SIZE }),
  new TextRun({ text: " (Version 4.5.3). R Foundation for Statistical Computing. https://www.R-project.org/", font: FONT, size: SIZE })],
  indent: { left: 360, hanging: 360 }, spacing: { after: 100, line: 300 } }) });
refParas.sort((x, y) => x.key.localeCompare(y.key, "en", { sensitivity: "base" }));

// ---------------------------------------------------------------- assemble
const body = [];
body.push(new Paragraph({ children: [new TextRun({ text: TITLE, bold: true, font: FONT, size: 28 })], spacing: { after: 240 } }));
body.push(P("Sahil Seikh¹  [add co-authors]", { alignment: AlignmentType.LEFT }));
body.push(P("¹ Department of Zoology, B. Borooah College (Autonomous), Guwahati, Assam, India", { alignment: AlignmentType.LEFT }));
body.push(P("Corresponding author: Sahil Seikh, sahilseikh132@gmail.com (ORCID: [add])", { alignment: AlignmentType.LEFT }));
body.push(H1("Abstract"), P(abstract));
body.push(P(`**Keywords** ${keywords}`, { alignment: AlignmentType.LEFT }));
body.push(H1("Introduction"), ...intro.map((x) => P(x)));
body.push(H1("Materials and methods"));
for (const [h, txt] of methods) body.push(H2(h), P(txt));
body.push(H1("Results and discussion"));
const FIGS = {
  "Sequencing depth and data processing": [
    () => TABLE(1, `Sequencing and processing summary: read pairs remaining after each step and the share of raw pairs retained`,
      ["Marker — wetland", "Raw", "Primers", "Filtered", "Merged", "Non-chimeric", "Curated", "% retained"],
      table1Rows, [2300, 900, 900, 900, 900, 1100, 900, 1000]),
    () => FIG(1, "Read processing and sequencing depth. **a** Read pairs remaining after each processing step for each marker and wetland. **b** Rarefaction curves of curated amplicon sequence variants (ASVs); curves reaching a plateau indicate sufficient sequencing depth")],
  "Taxonomic resolution and the reference-library gap": [
    () => FIG(2, "Identity of the unassigned COI ASVs to the closest known sequence at DNA level (open circles; GenBank, BLASTn) and protein level (filled circles; translated CO1 Reference Set, DIAMOND). Labels give the consensus phylum/class of the closest proteins; 'mixed' indicates no agreement")],
  "Community composition and ecological roles": [
    () => FIG(3, "Community composition. **a** Share of 18S rRNA reads by ecological role. **b** Share of COI reads by animal group, combining reference-set and protein-level assignments"),
    () => FIG(4, "The 30 most abundant named genera from both markers, as percentage of all reads of the respective marker in each wetland, ordered from Chandubi-leaning (top) to Deepor-leaning (bottom)")],
  "Diversity and overlap between wetlands": [
    () => TABLE(2, "Alpha diversity after rarefaction to equal depth per marker (mean of 100 subsamples)",
      ["Marker — wetland", "Depth", "ASVs", "Shannon", "Simpson", "Pielou", "Hill q1", "Hill q2"],
      table2Rows, [2300, 1000, 900, 900, 1000, 900, 1000, 1000]),
    () => FIG(5, "Diversity and overlap. **a** Alpha diversity as effective numbers of ASVs (richness, Hill q1, Hill q2). **b** Share of ASVs, named genera and named species found only in Chandubi Beel, in both wetlands, or only in Deepor Beel; numbers are counts")],
  "Biological indicators of trophic state": [
    () => TABLE(3, "Indicator taxa and their share of reads (%) of the respective marker in each wetland",
      ["Taxon", "Marker", "Group", "Chandubi", "Deepor"], table3Rows, [3100, 900, 1700, 1100, 1100],
      "Indicator associations follow the general water-quality literature; percentages are relative read abundance"),
    () => FIG(6, "Rotifer genera represented by species-level units (COI ASVs clustered at 97% identity) in each wetland. The Brachionus:Trichocerca quotient (QB/T) is given in the text")],
  "Agreement with microscopy": [
    () => FIG(7, "Taxa reported by microscopy in Deepor Beel (rotifers: Sharma, 2010; algae: Baruah et al., 2020) and whether they were also detected by eDNA")],
};
for (const [h, paras] of results) {
  body.push(H2(h), ...paras.map((x) => P(x)));
  for (const f of FIGS[h] || []) body.push(...f());
}
body.push(H1("Conclusions"), P(conclusions));
for (const [h, txt] of declarations) body.push(H1(h), P(txt));
body.push(H1("References"), ...refParas.map((r) => r.p));

const doc = new Document({
  creator: "Sahil Seikh",
  title: TITLE,
  styles: { default: { document: { run: { font: FONT, size: SIZE } } },
            paragraphStyles: [
              { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { bold: true, size: 22, font: FONT }, paragraph: { outlineLevel: 0 } },
              { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
                run: { size: SIZE, font: FONT }, paragraph: { outlineLevel: 1 } }] },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      lineNumbers: { countBy: 1, restart: LineNumberRestartFormat.CONTINUOUS },
    },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: SIZE })] })] }) },
    children: body,
  }],
});

const out = R("results/12_manuscript/Manuscript_EMAS.docx");
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(out, b); console.log(`wrote ${out} (figures ${figs.join(", ")})`); });
