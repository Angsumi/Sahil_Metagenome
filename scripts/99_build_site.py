#!/usr/bin/env python3
"""Final step — Build the GitHub Pages site (docs/index.html) from the scripts, result
tables and figures produced by steps 1–13. The page is a plain-language timeline;
scripts and full tables sit in collapsible "for specialists" panels. Standard library only."""
import csv
import html
import json
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO = "https://github.com/Angsumi/Sahil_Metagenome"
BLOB = f"{REPO}/blob/main"


def esc(s):
    return html.escape(str(s))


def rows(path):
    return list(csv.DictReader(open(ROOT / path), delimiter="\t"))


def fmt(n):
    return f"{int(float(n)):,}"


def table(path, rename=None):
    data = list(csv.reader(open(ROOT / path), delimiter="\t"))
    head, body = data[0], data[1:]
    rename = rename or {}
    out = ["<div class='tbl'><table><thead><tr>"]
    out += [f"<th>{esc(rename.get(h, h))}</th>" for h in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        cells = []
        for v in r:
            try:
                f = float(v)
                txt = f"{int(f):,}" if f.is_integer() and abs(f) >= 1000 else v
                cells.append(f"<td class='n'>{esc(txt)}</td>")
            except ValueError:
                cells.append(f"<td>{esc(v)}</td>")
        out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</tbody></table></div>")
    out.append(f"<p class='src'><a href='{BLOB}/{path}'>{esc(path)}</a></p>")
    return "".join(out)


def script(path):
    code = (ROOT / path).read_text()
    return (f"<details class='code'><summary><span>Script</span> <code>{esc(path)}</code></summary>"
            f"<pre><code>{esc(code)}</code></pre>"
            f"<p class='src'><a href='{BLOB}/{path}'>View on GitHub</a></p></details>")


def fig(name, caption):
    return (f"<figure><a href='img/{name}' target='_blank'><img src='img/{name}' alt='{esc(caption)}' loading='lazy'></a>"
            f"<figcaption>{caption}</figcaption></figure>")


def stats(*items):
    cells = "".join(f"<div class='stat'><b>{v}</b><span>{esc(k)}</span></div>" for v, k in items)
    return f"<div class='stats'>{cells}</div>"


def specialist(*parts):
    return ("<details class='spec'><summary>For specialists — scripts, parameters &amp; full tables</summary>"
            f"<div class='spec-body'>{''.join(parts)}</div></details>")


def files(*paths):
    items = "".join(f"<li><a href='{BLOB}/{p}'>{esc(p)}</a></li>" for p in paths)
    return f"<p class='label'>Output files</p><ul class='files'>{items}</ul>"


# ---- numbers ----
read_stats = rows("results/01_qc/read_stats.tsv")
raw_pairs = sum(int(r["reads"]) for r in read_stats if r["read"] == "R1")
cut = rows("results/02_primer_removal/cutadapt_summary.tsv")
cut_pct = 100 * sum(int(r["pairs_with_both_primers"]) for r in cut) / sum(int(r["pairs_in"]) for r in cut)
track = rows("results/05_summary/read_tracking.tsv")
final_pairs = sum(int(r["curated"]) for r in track)
asv = {r["marker"]: r for r in rows("results/05_summary/asv_counts.tsv")}
dada = {m: json.load(open(ROOT / f"results/03_dada2/{m}/summary.json")) for m in ("18S", "COI")}
frame = (ROOT / "results/04_curation/COI_frame.txt").read_text().strip()
kept = {m: int(asv[m]["total_asvs"]) for m in ("18S", "COI")}
removed = {m: dada[m]["asvs_final"] - kept[m] for m in ("18S", "COI")}

(DOCS / "reports").mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "results/01_qc/multiqc/multiqc_raw.html", DOCS / "reports/multiqc_raw.html")

# ---- timeline entries: (id, kicker, title, body) ----
steps = []

steps.append(("field", "Before the computer", "Water, DNA and a sequencing machine", f"""
<p>Every living thing sheds DNA into the water around it — skin cells, mucus, waste, whole tiny bodies.
A single bottle of lake water therefore carries a genetic trace of the community living there.
This approach is called <strong>environmental DNA (eDNA)</strong>.</p>
<p>Deepor Beel lies right beside Guwahati’s municipal solid-waste dumping ground, while Chandubi Beel has no comparable pressure — so comparing the two shows what that pressure does to the life in the water. No water chemistry was measured; instead, the organisms themselves serve as indicators of water condition (Steps 9 and 11).</p>
<p>Water was collected from each lake, the DNA extracted, and two short <em>barcode</em> genes copied
millions of times and read by an Illumina MiSeq sequencer at Eurofins Genomics:</p>
<div class='pair'>
  <div><h4>18S rRNA</h4><p>A barcode shared by almost all complex life. It catches <strong>microscopic algae, protists
  and fungi</strong> as well as small animals — the base of the food web.</p></div>
  <div><h4>COI</h4><p>The classic “animal barcode”. It catches <strong>zooplankton</strong> — rotifers,
  water fleas, copepods, mites and insect larvae.</p></div>
</div>
<p>The machine returns its output as text files of DNA letters (A, C, G, T). Everything below is about turning
those raw files into a clean, trustworthy list of the distinct DNA signatures present in each lake.</p>
"""))

steps.append(("qc", "Step 1", "Checking the raw data", f"""
<p class='plain'><span>In plain words</span>Before using any data you check it arrived intact and is of good quality —
like checking a set of photos for damage and blur before choosing which to print.</p>
<p>Each file’s digital fingerprint (checksum) was compared to the one supplied by the lab: all eight match,
so nothing was corrupted in transfer. Each DNA fragment is read from both ends, giving two 301-letter
<em>reads</em> per fragment. The machine’s confidence is high for most of the read but fades towards the
end, especially on the second read — so the tail ends will be trimmed in step 3.</p>
{stats(("8 / 8", "files intact"), (fmt(raw_pairs), "DNA fragments read"), ("2 × 301", "letters per fragment"))}
{fig("01_quality_18S.png", "<b>How to read this:</b> left to right is position along the read; height is the machine’s confidence "
     "(above 30 = fewer than 1 error in 1,000 letters). The green line holds up on the left panels (first read) but "
     "sinks on the right (second read) after about letter 230.")}
{specialist(
    "<p>Checksums vs vendor <code>MD5SUM_Raw.txt</code>; FastQC + MultiQC; per-file read statistics; "
    "DADA2 quality profiles (50,000 reads per file). All files come from one MiSeq run, "
    "<code>M04635:72:000000000-MDYKK</code>.</p>",
    script("scripts/01_qc.sh"), script("scripts/01_quality_profiles.R"),
    table("results/01_qc/md5_check.tsv"),
    table("results/01_qc/read_stats.tsv", {"mean_len": "mean length", "gc_pct": "GC %", "mean_q": "mean Q"}),
    fig("01_quality_COI.png", "COI quality profiles."),
    "<p><a href='reports/multiqc_raw.html'>Full MultiQC report →</a></p>")}
"""))

steps.append(("primers", "Step 2", "Removing the copying labels", f"""
<p class='plain'><span>In plain words</span>To copy a barcode gene, the lab uses short “starter” pieces of DNA
called <em>primers</em> — think of them as address labels stuck to each end. They are not part of the organism’s DNA,
so they are cut off. Any fragment missing its labels was copied by mistake and is thrown away.</p>
<p>Nearly nine in ten fragments carried both labels exactly where expected — a sign the lab work went well.
The primers were identified by reading the data itself, not taken on trust.</p>
{stats((f"{cut_pct:.0f}%", "fragments kept"), ("2", "primer pairs found"), ("~280", "letters left per read"))}
{fig("02_primer_retention.png", "Blue: fragments that carried both labels and were kept. Grey: discarded. "
     "Both lakes and both barcodes behave alike.")}
{specialist(
    "<div class='tbl'><table><thead><tr><th>Marker</th><th>Forward</th><th>Reverse</th><th>Reference</th></tr></thead><tbody>"
    "<tr><td>18S V4</td><td>E572F <code>CYGCGGTAATTCCAGCTC</code></td><td>E1009R <code>AYGGTATCTRWTCRTCTTYG</code></td><td>Comeau et al. 2011</td></tr>"
    "<tr><td>COI</td><td>mlCOIintF <code>GGWACWGGWTGAACWGTWTAYCCYCC</code></td><td>jgHCO2198 <code>TANACYTCNGGRTGNCCRAARAAYCA</code></td><td>Leray et al. 2013</td></tr>"
    "</tbody></table></div><p>Cutadapt linked adapters: 5′ primer anchored and required, read-through primer optional; "
    "max error 0.15; untrimmed pairs discarded.</p>",
    script("scripts/02_primer_removal.sh"), script("scripts/02_plot_lengths.R"),
    table("results/02_primer_removal/cutadapt_summary.tsv",
          {"pairs_in": "pairs in", "pairs_with_both_primers": "kept", "pct_kept": "% kept"}),
    fig("02_trimmed_lengths.png", "Read lengths after primer removal (log scale)."))}
"""))

steps.append(("dada2", "Step 3", "Separating real DNA from typos", f"""
<p class='plain'><span>In plain words</span>Sequencers make occasional typos. If you counted every slightly different
spelling as a new organism you would invent thousands of species that don’t exist. This step learns the machine’s
typo habits from the data itself, then decides which sequences are real and which are just misspellings of them.</p>
<p>What survives is a list of <strong>ASVs</strong> (amplicon sequence variants) — each one an exact, unique DNA signature,
roughly “one distinct kind of organism”. The two reads of each fragment are then joined into one full sequence, and
<em>chimeras</em> — artificial sequences glued together from two different organisms during copying — are removed.</p>
<p>Importantly, <strong>both lakes were processed together</strong>, so the same organism gets the same signature in
both lakes and they can be compared fairly.</p>
{stats((fmt(dada['18S']['asvs_final']), "18S signatures"), (fmt(dada['COI']['asvs_final']), "COI signatures"),
       (f"{dada['18S']['chimeric_read_pct']}%", "18S reads were chimeras"))}
{fig("03_errors_COI_R1.png", "<b>The typo model.</b> Each panel is one kind of substitution (e.g. A read as C). Dots are "
     "observed error rates; the black line is the model learned from the data. They agree, and errors fall as the machine’s "
     "confidence (x-axis) rises — the model can be trusted.")}
{specialist(
    "<div class='tbl'><table><thead><tr><th>Parameter</th><th>18S</th><th>COI</th></tr></thead><tbody>"
    f"<tr><td>truncLen (R1, R2)</td><td>{dada['18S']['truncLen'][0]}, {dada['18S']['truncLen'][1]}</td><td>{dada['COI']['truncLen'][0]}, {dada['COI']['truncLen'][1]}</td></tr>"
    "<tr><td>maxEE (R1, R2)</td><td>2, 4</td><td>2, 4</td></tr>"
    "<tr><td>Denoising</td><td colspan='2'>pooled across both sites (<code>pool = TRUE</code>)</td></tr>"
    "<tr><td>Merging</td><td colspan='2'>minOverlap 12, maxMismatch 0</td></tr>"
    f"<tr><td>ASVs before → after chimera removal</td><td>{dada['18S']['asvs_before_chimera']} → {dada['18S']['asvs_final']}</td><td>{dada['COI']['asvs_before_chimera']} → {dada['COI']['asvs_final']}</td></tr>"
    "</tbody></table></div>",
    script("scripts/03_dada2.R"),
    "<h4>18S read tracking</h4>", table("results/03_dada2/18S/track.tsv"),
    "<h4>COI read tracking</h4>", table("results/03_dada2/COI/track.tsv"),
    "<div class='grid'>", fig("03_errors_18S_R1.png", "18S R1"), fig("03_errors_18S_R2.png", "18S R2"),
    fig("03_errors_COI_R1.png", "COI R1"), fig("03_errors_COI_R2.png", "COI R2"), "</div>",
    files("results/03_dada2/18S/asv_table.tsv", "results/03_dada2/18S/asv_seqs.fasta",
          "results/03_dada2/COI/asv_table.tsv", "results/03_dada2/COI/asv_seqs.fasta"))}
"""))

steps.append(("curation", "Step 4", "Weeding out fakes", f"""
<p class='plain'><span>In plain words</span>The COI barcode is a recipe for a protein. A genuine recipe reads like a
sentence with no “STOP” in the middle. Sequences that contain a stop, or whose length breaks the three-letter
rhythm of the code, are broken copies (old “ghost” genes or errors) and are removed. For 18S, sequences far too
short or too long to be the real barcode are removed.</p>
<p>Very little had to go — the data was already clean after step 3.</p>
{stats((f"{removed['COI']}", "COI fakes removed"), (f"{removed['18S']}", "18S off-length removed"),
       (f"{kept['18S'] + kept['COI']:,}", "signatures kept"))}
{fig("04_curation.png", "Each dot is one DNA signature: how long it is (x) and how common (y, log scale). "
     "Blue were kept. The kept COI signatures line up neatly at 313 and 316 letters — exactly the expected size, "
     "differing by one three-letter “word”.")}
{specialist(
    f"<p>COI: length must differ from 313 bp by whole codons (±10) and translate stop-free under NCBI genetic code 5 "
    f"(invertebrate mitochondrial); {esc(frame.lower())}. 18S: 350–480 bp.</p>",
    script("scripts/04_asv_curation.R"),
    table("results/04_curation/curation_summary.tsv", {"W1_reads": "Chandubi reads", "W2_reads": "Deepor reads"}),
    files("results/04_curation/18S_asv_table_curated.tsv", "results/04_curation/18S_asv_seqs_curated.fasta",
          "results/04_curation/COI_asv_table_curated.tsv", "results/04_curation/COI_asv_seqs_curated.fasta"))}
"""))

c18, cco = asv["18S"], asv["COI"]
steps.append(("summary", "Step 5", "What we ended up with", f"""
<p class='plain'><span>In plain words</span>A final check: how much of the raw data made it through, how many
signatures each lake has, and — the key question — did we sequence deeply enough to find nearly everything?</p>
{stats((f"{100*final_pairs/raw_pairs:.0f}%", "of raw data used"), (fmt(c18['total_asvs']), "18S signatures"),
       (fmt(cco['total_asvs']), "COI signatures"))}
{fig("05_rarefaction.png", "<b>Did we look hard enough?</b> Like a birdwatcher counting new species: at first every few minutes "
     "brings a new one, later almost none. Each line climbs quickly then flattens — sequencing more would have found "
     "very few new signatures. Depth was sufficient in both lakes for both barcodes.")}
{fig("05_asv_counts.png", "Signatures found only in Chandubi (blue), only in Deepor (orange), and the ones in both lakes (grey).")}
{fig("05_read_tracking.png", "How many DNA fragments remained after each step.")}
{specialist(
    script("scripts/05_summary.R"),
    table("results/05_summary/read_tracking.tsv",
          {"primers_found": "primers found", "nonchim": "non-chimeric", "pct_retained": "% of raw retained"}),
    table("results/05_summary/asv_counts.tsv",
          {"W1_asvs": "Chandubi", "W2_asvs": "Deepor", "shared_asvs": "shared", "total_asvs": "total",
           "shared_reads_pct_W1": "% Chandubi reads shared", "shared_reads_pct_W2": "% Deepor reads shared",
           "bray_curtis": "Bray–Curtis", "jaccard": "Jaccard"}))}
"""))


# ---- taxonomy numbers ----
tsum = {r["marker"]: r for r in rows("results/06_taxonomy/taxonomy_summary.tsv")}
depth = {(r["marker"], r["rank"]): r for r in rows("results/06_taxonomy/assignment_depth.tsv")}
blast = rows("results/06_taxonomy/COI_blast_unknowns_summary.tsv")
# Rotifer share with library names + BLAST look-ups, without double counting (from step 9)
rot_total = {r["group"]: r for r in rows("results/09_ecology/COI_animal_groups.tsv")}["Rotifers"]
rot_total = {k: float(rot_total[k]) for k in ("W1", "W2")}
top = next(r for r in blast if r["asv"] == "COI_ASV0001")
div18 = (min(float(depth[("18S", "Division")][s]) for s in ("W1", "W2")),
         max(float(depth[("18S", "Division")][s]) for s in ("W1", "W2")))
TAXDIR = "results/06_taxonomy"

steps.append(("taxonomy", "Step 6", "Putting names to the signatures", f"""
<p class='plain'><span>In plain words</span>Each signature is still just a string of DNA letters. To name it, we compare
it with large public libraries of DNA from organisms that experts have already identified — like matching a
fingerprint against a database. A name is accepted only when the match is both <em>confident</em> and
<em>close enough</em>: a species name, for example, needs the sequence to be at least 97–99% identical to a known one.
If the match is weaker, we only claim a broader group (a family, or just “a rotifer”).</p>
{stats((f"{div18[0]:.0f}–{div18[1]:.0f}%", "18S reads named to major group"),
       (fmt(tsum['18S']['named_genera']), "18S genera named"),
       (fmt(tsum['COI']['named_genera']), "COI genera named"))}
<h4>What lives where (18S — the microscopic community)</h4>
<div class='pair'>
  <div><h4>Chandubi Beel</h4><p>Rich in <strong>green algae</strong> (Chlorophyceae, ~14% of reads), <strong>diatoms</strong>
  (<em>Cyclotella</em>, <em>Aulacoseira</em>, <em>Nitzschia</em>), small amoeboid <strong>cercozoans</strong>, <strong>ciliates</strong>
  and <strong>rotifers</strong>.</p></div>
  <div><h4>Deepor Beel</h4><p>Dominated by <strong>fungi</strong> (incl. chytrids that infect algae), <strong>desmids</strong> — ornate
  green algae such as <em>Staurastrum</em> and <em>Cosmarium</em> (~15%), <strong>water moulds</strong> (oomycetes),
  <strong>gastrotrichs</strong> and <strong>nematodes</strong>.</p></div>
</div>
{fig("06_18S_division.png", "Share of 18S reads in each major group. The two lakes look strikingly different: Chandubi is "
     "algae-and-protist rich, Deepor fungus- and desmid-rich.")}
<h4>Zooplankton (COI)</h4>
<p>Rotifers dominate the named animals in both lakes — <em>Brachionus caudatus</em>, <em>B. calyciflorus</em>,
<em>Keratella tropica</em> and <em>Polyarthra vulgaris</em> among them. <strong>Copepods are present</strong>:
<em>Mesocyclops</em> (both lakes), <em>Microcyclops</em> and <em>Eucyclops</em> appear in the 18S data and a trace of
<em>Mesocyclops</em> in COI — the lab’s earlier report found none. Water fleas (cladocerans) were not detected.</p>
<p>But most COI reads could not be named at all: only {float(depth[('COI','Phylum')]['W1']):.0f}% (Chandubi) and
{float(depth[('COI','Phylum')]['W2']):.0f}% (Deepor) reach even phylum level. Their closest library matches are only 70–85% identical —
too distant to name. Step 7 looks into them.</p>
{fig("06_identity.png", "How similar each sequence is to its closest relative in the library (bars weighted by reads). "
     "18S piles up near 100% — well known organisms. COI is split: one peak near 98% (named rotifers) and a large mass "
     "between 70 and 85% — organisms with no close relative in the library.")}
{fig("06_assignment_depth.png", "Share of reads that could be named at each level, from broad (left) to precise (right).")}
{specialist(
    "<div class='tbl'><table><thead><tr><th></th><th>18S</th><th>COI</th></tr></thead><tbody>"
    "<tr><td>Reference</td><td>PR2 v5.1.1 (SSU, UTAX format)</td><td>Eukaryote CO1 Reference Set v5.1.0 (Porter &amp; Hajibabaei)</td></tr>"
    "<tr><td>Classifier</td><td colspan='2'>VSEARCH SINTAX, bootstrap cutoff 0.80, both strands</td></tr>"
    "<tr><td>Closest hit</td><td colspan='2'>VSEARCH global alignment, top hit % identity</td></tr>"
    "<tr><td>Minimum identity</td><td>family 95 · genus 97 · species 99 %</td><td>order 85 · family 90 · genus 95 · species 97 %</td></tr>"
    "</tbody></table></div><p>Ranks are accepted top-down; PR2 placeholder names (<code>_X</code>, <code>_sp.</code>) are "
    "left blank but do not block lower ranks. MIDORI2 was the intended COI reference, but its Zenodo host refused "
    "downloads from this network.</p>",
    script("scripts/06_taxonomy.sh"), script("scripts/06_taxonomy.R"),
    table(f"{TAXDIR}/taxonomy_summary.tsv"),
    table(f"{TAXDIR}/assignment_depth.tsv"),
    fig("06_18S_class.png", "18S, class level."),
    "<div class='grid'>", fig("06_COI_phylum.png", "COI, phylum level."), fig("06_COI_class.png", "COI, class level."), "</div>",
    files(f"{TAXDIR}/18S_taxonomy.tsv", f"{TAXDIR}/COI_taxonomy.tsv", f"{TAXDIR}/named_genera_species.tsv",
          f"{TAXDIR}/18S_composition_division.tsv", f"{TAXDIR}/18S_composition_class.tsv",
          f"{TAXDIR}/COI_composition_phylum.tsv", f"{TAXDIR}/COI_composition_class.tsv"))}
"""))

steps.append(("blast", "Step 7", "Looking up the unknowns in GenBank", f"""
<p class='plain'><span>In plain words</span>The COI library used in step 6 is curated and so leaves things out. GenBank,
run by the US National Center for Biotechnology Information (NCBI), holds nearly every DNA sequence ever published.
We searched it (with a tool called BLAST) for the 40 most abundant COI signatures that step 6 could not name —
together about {sum(float(r['reads_pct_W1']) for r in blast):.0f}% of Chandubi’s and
{sum(float(r['reads_pct_W2']) for r in blast):.0f}% of Deepor’s COI reads.</p>
<p><strong>Most of them are rotifers</strong> that simply aren’t in reference libraries yet. Several match unnamed
“rotifer environmental samples” almost exactly (98–100%), sequences found by other studies but never tied to a named species;
others are 80–89% similar to known rotifers such as <em>Brachionus</em>, <em>Trichocerca</em> and <em>Anuraeopsis</em> —
likely related species that have never been barcoded. Counting these, rotifers make up roughly
<strong>{rot_total['W1']:.0f}%</strong> of Chandubi’s and <strong>{rot_total['W2']:.0f}%</strong> of Deepor’s COI reads.</p>
<p><strong>The single most common COI signature is a true unknown.</strong> {top['asv']} accounts for
{float(top['reads_pct_W1']):.0f}% (Chandubi) and {float(top['reads_pct_W2']):.0f}% (Deepor) of COI reads, reads cleanly as a protein-coding gene,
yet nothing in all of GenBank is more than about 72% identical to it. It belongs to an organism whose DNA has never been sequenced
— possibly a new or unstudied local species.</p>
{stats((f"{rot_total['W1']:.0f}% / {rot_total['W2']:.0f}%", "COI reads that are rotifers (Chandubi / Deepor)"),
       ("~72%", "best match for the top unknown"), ("40", "sequences searched"))}
{fig("06b_blast_unknowns.png", "The 25 most abundant ‘unknowns’ and their closest match in GenBank, with % identity. "
     "Above ~97%: same species. 80–90%: a relative in the same group. Below 80%: no meaningful relative on record.")}
{specialist(
    "<p>NCBI BLAST URL API, database <code>core_nt</code>, megablast (E ≤ 1e-20, 5 hits per query); queries with no "
    "megablast hit re-run with blastn (word size 11). Best hit = highest identity × query cover. Lineage from NCBI Taxonomy "
    "(E-utilities). Hits below 80% identity are not assigned to any group.</p>",
    script("scripts/06b_blast_unknowns.sh"), script("scripts/06b_ncbi_blast.py"), script("scripts/06b_blast_summary.R"),
    table(f"{TAXDIR}/COI_blast_unknowns_by_group.tsv"),
    files(f"{TAXDIR}/COI_blast_unknowns_summary.tsv", f"{TAXDIR}/COI_blast_unknowns.tsv"))}
"""))


# ---- diversity & ecology numbers ----
alpha = {(r["marker"], r["sample"]): r for r in rows("results/08_diversity/alpha_diversity.tsv")}
ovl = {(r["marker"], r["level"]): r for r in rows("results/08_diversity/overlap_by_level.tsv")}
roles = {r["role"]: r for r in rows("results/09_ecology/18S_ecological_roles.tsv")}
cgrp = {r["group"]: r for r in rows("results/09_ecology/COI_animal_groups.tsv")}
amark = rows("results/09_ecology/animal_genera_by_marker.tsv")
n_by = {k: sum(1 for r in amark if r["detected_by"] == k) for k in ("18S only", "COI only", "both")}
ECO = "results/09_ecology"
DIV = "results/08_diversity"


def a(m, s, k, d=0):
    return f"{float(alpha[(m, s)][k]):.{d}f}"


def algae(s):
    return sum(float(roles[r][s]) for r in ("Green algae", "Desmids & conjugating algae", "Diatoms",
                                             "Golden & other algae", "Dinoflagellates"))


steps.append(("diversity", "Step 8", "How diverse is each lake?", f"""
<p class='plain'><span>In plain words</span>Diversity has two sides: <em>how many kinds</em> there are, and <em>how evenly</em>
they are spread. A lake with 100 kinds where one makes up 90% of everything is less diverse in practice than one with 100
equally common kinds. To compare fairly, both lakes are first cut down to the same number of reads — like comparing two
birdwatchers who each watched for exactly one hour.</p>
<p>We report diversity as an <strong>effective number of types</strong>: “this community is as diverse as one with N equally
common types”. Counting every type gives the largest number; counting only the common ones gives a smaller one.</p>
{stats((f"{a('18S','W1','observed')} vs {a('18S','W2','observed')}", "18S types: Chandubi vs Deepor"),
       (f"{a('COI','W1','observed')} vs {a('COI','W2','observed')}", "COI types: Chandubi vs Deepor"),
       (f"{ovl[('18S','ASV')]['pct_shared']}% / {ovl[('COI','ASV')]['pct_shared']}%", "types shared (18S / COI)"))}
<p><strong>The two barcodes tell opposite stories.</strong> For algae, protists and fungi (18S), Deepor is clearly richer —
about {a('18S','W2','hill_q1')} effective types against {a('18S','W1','hill_q1')} in Chandubi. For zooplankton (COI),
Chandubi is slightly richer and more even ({a('COI','W1','hill_q1')} vs {a('COI','W2','hill_q1')}), because Deepor is more
dominated by a few rotifers.</p>
{fig("08_alpha.png", "Diversity of each lake, at three levels of strictness. Numbers are the effective number of equally common types.")}
<p>Looking at what the lakes share: by 18S, most types live in only one of the two lakes — even at genus level only
{ovl[('18S','Genus')]['pct_shared']}% of named genera occur in both. By COI, most types are shared.</p>
{fig("08_overlap.png", "Share of types found only in Chandubi, in both lakes, or only in Deepor — counted as exact sequences (ASV), "
     "named genera and named species. COI genus and species counts are small because few COI sequences could be named.")}
{specialist(
    "<p>Rarefied to the smaller lake’s depth per marker (18S 81,828; COI 102,761 reads), averaged over 100 random subsamples. "
    "Hill numbers: q0 = richness, q1 = exp(Shannon), q2 = inverse Simpson. Chao1 is not reported because DADA2 removes "
    "singletons. Jaccard and Bray–Curtis at genus/species level use only reads named at that level. "
    "One sample per lake: no significance tests are possible.</p>",
    script("scripts/08_diversity.R"),
    table(f"{DIV}/alpha_diversity.tsv", {"rarefied_to": "rarefied to", "hill_q1": "Hill q1", "hill_q2": "Hill q2"}),
    table(f"{DIV}/overlap_by_level.tsv", {"chandubi_only": "Chandubi only", "deepor_only": "Deepor only",
                                         "pct_shared": "% shared", "jaccard_similarity": "Jaccard",
                                         "bray_curtis_dissimilarity": "Bray–Curtis"}))}
"""))

steps.append(("ecology", "Step 9", "Reading the lakes’ ecology", f"""
<p class='plain'><span>In plain words</span>A list of names becomes useful when we ask what those organisms <em>do</em>:
who makes food from sunlight (algae), who eats (protozoa, animals), who recycles or infects (fungi, water moulds,
parasites). Some organisms are also well-known <em>indicators</em> — their presence hints at how nutrient-rich or polluted
water is.</p>
<h4>Who does what (18S)</h4>
<p>In Chandubi, about <strong>{algae('W1'):.0f}%</strong> of 18S reads come from algae — green algae and diatoms above all —
and another {float(roles['Protozoa (free-living)']['W1']):.0f}% from free-living protozoa: a community built on
<em>producers and grazers</em>. In Deepor, algae make up {algae('W2'):.0f}% (mostly desmids), while
<strong>fungi ({float(roles['Fungi']['W2']):.0f}%)</strong> and <strong>water moulds ({float(roles['Water moulds (oomycetes)']['W2']):.0f}%)</strong>
take a much larger share — a community leaning towards <em>decomposition and parasitism</em>, as expected where dead plant
material is plentiful.</p>
{fig("09_18S_roles.png", "Share of 18S reads by ecological role in each lake.")}
<h4>Zooplankton groups (COI, including the GenBank look-ups)</h4>
<p>Rotifers make up about <strong>{float(cgrp['Rotifers']['W1']):.0f}%</strong> (Chandubi) and
<strong>{float(cgrp['Rotifers']['W2']):.0f}%</strong> (Deepor) of COI reads. Crustaceans are scarce in this barcode — copepods,
ostracods and insects together are under 1%. About a fifth of reads remain unknown, the largest part being the single
unidentified organism found in Step 7.</p>
{fig("09_COI_groups.png", "Share of COI reads by animal group.")}
<h4>The main players</h4>
{fig("09_genera_heatmap.png", "The 30 most abundant named genera from both barcodes. Darker = more reads. "
     "Chandubi is marked by diatoms (<i>Cyclotella</i>, <i>Aulacoseira</i>) and green algae (<i>Desmodesmus</i>, <i>Chlamydomonas</i>); "
     "Deepor by water moulds (<i>Aphanomyces</i>), chytrid fungi (<i>Rhizophydium</i>), desmids (<i>Staurastrum</i>, <i>Cosmarium</i>) "
     "and golden algae. The rotifers <i>Brachionus</i> and <i>Keratella</i> are abundant in both.")}
<h4>Two barcodes see different animals</h4>
<p>Of the animal genera named, <strong>{n_by['18S only']}</strong> were found only by 18S (flatworms, gastrotrichs, oligochaete worms,
copepods <em>Eucyclops</em> and <em>Microcyclops</em>), <strong>{n_by['COI only']}</strong> only by COI (the main rotifers
<em>Brachionus</em>, <em>Keratella</em>, <em>Polyarthra</em>, <em>Asplanchna</em>, and the mayfly <em>Cloeon</em>), and just
{n_by['both']} by both (<em>Mesocyclops</em>). Using two barcodes roughly doubled the animal list — the main argument for a
multi-marker design.</p>
<h4>Indicator organisms</h4>
<p>Several organisms that ecologists use as water-quality signals were found. The picture is mixed rather than simple:</p>
<ul>
<li><strong>Nutrient-rich signals in both lakes:</strong> the rotifers <em>Brachionus</em> and <em>Keratella tropica</em> are
abundant everywhere and somewhat more so in Deepor. Chandubi additionally holds diatoms typical of enriched water
(<em>Cyclotella meneghiniana</em>, <em>Nitzschia palea</em>, <em>Aulacoseira granulata</em>).</li>
<li><strong>Deepor’s desmids</strong> (<em>Staurastrum</em>, <em>Cosmarium</em>) are a group often linked to plant-rich, less
enriched water — fitting a macrophyte-covered wetland — alongside chytrid parasites of algae.</li>
</ul>
<p>These are pointers rather than verdicts; read together they are consistent with nutrient enrichment, strongest at Deepor beside the dumping ground.</p>
{specialist(
    "<p>18S roles are assigned from PR2 division/class. COI groups use the reference-library phylum where available and the "
    "NCBI BLAST phylum (≥ 80% identity) for the 40 looked-up ASVs. Indicator notes in "
    f"<a href='{BLOB}/scripts/indicator_taxa.tsv'>scripts/indicator_taxa.tsv</a> are general associations from the "
    "water-quality literature, to be confirmed with regional sources before citing.</p>",
    script("scripts/09_ecology.R"),
    table(f"{ECO}/18S_ecological_roles.tsv"),
    table(f"{ECO}/COI_animal_groups.tsv"),
    table(f"{ECO}/indicator_taxa.tsv", {"chandubi_pct": "Chandubi %", "deepor_pct": "Deepor %",
                                       "general_association": "general association"}),
    table(f"{ECO}/animal_genera_by_marker.tsv", {"detected_by": "detected by"}),
    files(f"{ECO}/top_genera.tsv", f"{ECO}/18S_asv_roles.tsv", f"{ECO}/COI_asv_groups.tsv",
          f"{ECO}/animal_phyla_by_marker.tsv"))}
"""))

# ---- rotifer index, manuscript package, SRA ----
qbt = {r["sample"]: r for r in rows("results/11_rotifer_index/QBT_index.tsv")}
RI = "results/11_rotifer_index"
MS = "results/12_manuscript"
SRA = "results/13_sra"

# ---- protein-level identification ----
prot = rows("results/10_protein/COI_protein_summary.tsv")
pgrp = rows("results/10_protein/COI_protein_by_group.tsv")
PR = "results/10_protein"
prot_rot = next((g for g in pgrp if g["consensus_phylum"] == "Rotifera"), None)
a1 = next(r for r in prot if r["asv"] == "COI_ASV0001")

steps.append(("protein", "Step 10", "A second look at the unknowns — through their proteins", f"""
<p class='plain'><span>In plain words</span>COI is a recipe for a protein. Over evolution the DNA “spelling” changes much
faster than the protein it makes — many different spellings give the same protein. So two organisms whose DNA looks only
75% alike can still have very similar proteins, which reveals their family ties. We translated the unknown sequences into
protein and compared them with 2.2 million known COI proteins.</p>
{stats((f"{prot_rot['asvs'] if prot_rot else 0} of {len(prot)}", "unknowns that are rotifers"),
       (f"{float(prot_rot['W1_pct']):.0f}% / {float(prot_rot['W2_pct']):.0f}%" if prot_rot else "–",
        "COI reads they add (Chandubi / Deepor)"),
       (f"{float(a1['aa_identity']):.0f}%", "best protein match, top unknown"))}
<p><strong>Most unknowns are rotifers.</strong> Their proteins are 89–98% identical to known rotifers such as
<em>Trichocerca</em>, <em>Euchlanis</em>, <em>Filinia</em>, <em>Lecane</em> and <em>Brachionus</em> — confirming that the
lakes hold many rotifer species whose DNA has never been catalogued. A few others point to mites, an ostracod, a
freshwater sponge and an amoeba.</p>
<p><strong>The most common COI signature remains a mystery.</strong> {a1['asv']}’s protein is closest to a nematode
(roundworm, {float(a1['aa_identity']):.0f}% identical) but almost as close to brown-algae-like stramenopiles (~81%). The evidence
does not settle which group it belongs to — it may be an organism from a group that has barely been sequenced. Isolating and
sequencing it (or its full mitochondrial genome) would be needed to name it.</p>
{fig("10_protein.png", "For each unknown: similarity to the closest known sequence at DNA level (orange) and protein level (blue). "
     "Protein similarity is much higher, which is what lets us place most of them. Label: group agreed by the closest proteins.")}
{specialist(
    "<p>The Eukaryote CO1 Reference Set v5.1.0 was translated with SeqKit (genetic code 5; for each sequence the frame "
    "with fewest stop codons) and indexed with DIAMOND v2.2.8. Queries: the COI ASVs from step 7 without a ≥ 90% GenBank DNA "
    "match. DIAMOND blastx <code>--ultra-sensitive</code>, query genetic code 5, E ≤ 1e-10, 25 targets. Consensus phylum/class: "
    "≥ 3 hits within 95% of the best bit score and ≥ 70% agreement. NCBI’s online BLASTx was tried first but its queue did "
    "not return results.</p>",
    script("scripts/10_protein_search.sh"), script("scripts/10_protein_summary.R"),
    table(f"{PR}/COI_protein_by_group.tsv", {"consensus_phylum": "phylum", "consensus_class": "class",
                                           "W1_pct": "Chandubi %", "W2_pct": "Deepor %"}),
    files(f"{PR}/COI_protein_summary.tsv", f"{PR}/COI_protein_hits.tsv"))}
"""))

steps.append(("rotifers", "Step 11", "A rotifer signal of nutrient levels", f"""
<p class='plain'><span>In plain words</span>Rotifers are useful messengers. A classic rule of thumb compares two rotifer
genera: <em>Brachionus</em>, which thrives in nutrient-rich water, and <em>Trichocerca</em>, more typical of cleaner water.
Dividing the number of <em>Brachionus</em> species by the number of <em>Trichocerca</em> species gives the
<strong>QB/T index</strong>: below 1 suggests nutrient-poor water, 1–2 moderate, above 2 nutrient-rich.</p>
<p>Few COI sequences can be named to species, so “species” here are clusters of sequences that are at least 97% identical —
a standard stand-in for species with this barcode.</p>
{stats((qbt['W1']['QBT'], "QB/T Chandubi"), (qbt['W2']['QBT'], "QB/T Deepor"),
       (f"{qbt['W1']['rotifer_motus']} / {qbt['W2']['rotifer_motus']}", "rotifer species-clusters (Chandubi / Deepor)"))}
<p>Both lakes score well above 2 — <strong>a nutrient-rich (eutrophic) signal in both</strong>, with about
{qbt['W1']['brachionus_motus']} <em>Brachionus</em> clusters against {qbt['W1']['trichocerca_motus']} <em>Trichocerca</em>.
Treat the exact value as provisional: several genus names come only from distant GenBank matches (80–90%).</p>
{fig("11_rotifer_genera.png", "Number of species-level clusters in each rotifer genus, per lake.")}
{specialist(
    "<p>COI ASVs clustered at 97% with VSEARCH <code>--cluster_size</code> (abundance-sorted). MOTU genus from the "
    "reference-library genus of any member ASV, otherwise the genus of the best NCBI BLAST hit at ≥ 80% identity "
    "(provisional). QB/T after Sládeček (1983).</p>",
    script("scripts/11_rotifer_index.sh"), script("scripts/11_rotifer_index.R"),
    table(f"{RI}/QBT_index.tsv"),
    table(f"{RI}/rotifer_genera_by_lake.tsv"),
    files(f"{RI}/COI_motus.tsv", f"{RI}/COI_motu97.uc"))}
"""))

steps.append(("paper", "Steps 12, 13, 16", "Files for the paper", f"""
<p class='plain'><span>In plain words</span>Everything above, packaged the way a journal and the public DNA archive expect it:
figures at print resolution, tables, a draft Methods section, and the forms needed to deposit the raw data.</p>
<h4>Manuscript package</h4>
<ul class='files'>
<li><a href='{REPO}/raw/main/{MS}/Manuscript_EMAS.docx'><b>Full manuscript (Word)</b></a> — formatted for <em>Environmental Monitoring and Assessment</em>: 10-pt Times, line numbers, embedded figures and tables, APA references verified against Crossref</li>
<li>Figures 1–7 for submission (TIFF, 600 dpi, 174 mm wide; also PDF and PNG): <a href='{REPO}/tree/main/{MS}/figures'>{MS}/figures</a></li>
<li>Tables 1–5 (CSV): <a href='{REPO}/tree/main/{MS}/tables'>{MS}/tables</a></li>
<li><a href='{REPO}/raw/main/{MS}/tables/Supplementary_Tables_S1-S12.xlsx'>Supplementary Tables S1–S12 (Excel)</a> and ASV FASTA files</li>
</ul>
<h4>NCBI SRA submission</h4>
<p>Two BioSamples (one per lake) and four sequencing runs (two barcodes × two lakes). Because both barcodes use the same file
names, the eight files get unique names for upload (e.g. <code>COI_Deepor_Beel_W2_R1.fastq.gz</code>).</p>
<ul class='files'>
<li><a href='{BLOB}/{SRA}/biosample_MIMARKS_survey_water.tsv'>BioSample sheet</a> (MIMARKS survey, water package) — only the coordinates remain to fill in</li>
<li><a href='{BLOB}/{SRA}/sra_metadata.tsv'>SRA metadata sheet</a> with file names and MD5 checksums</li>
</ul>
{specialist(script("scripts/12_manuscript.R"), script("scripts/16_manuscript_docx.js"), script("scripts/13_sra_prep.py"))}
"""))

# ---- references and microscopy comparison ----
refs = rows("results/14_references/references_verified.tsv")
n_ver = sum(1 for r in refs if r["status"].startswith(("VERIFIED", "FOUND")))
n_bad = len(refs) - n_ver
cmp_rows = rows("results/15_microscopy/comparison_summary.tsv")
rotm = rows("results/15_microscopy/rotifers_microscopy_vs_DNA.tsv")
algm = rows("results/15_microscopy/algae_genera_microscopy_vs_DNA.tsv")
alg_both = [r["genus"] for r in algm if r["found_by"] == "both"]
desmids_both = [r["genus"] for r in algm if r["found_by"] == "both" and r["role"].startswith("Desmids")]
alg_dna_only = sum(1 for r in algm if r["found_by"] == "DNA only")
alg_blind = sum(1 for r in algm if r["found_by"] == "microscopy only" and r["note"])
MI = "results/15_microscopy"
REF = "results/14_references"

steps.append(("references", "Step 14", "Checking every reference", f"""
<p class='plain'><span>In plain words</span>A reference list is only as good as its weakest entry. Every work cited in the
draft and in the Methods was looked up in Crossref, the registry behind DOIs, and its title, first author and year compared
with what we cite. The final list is built from those records, not typed by hand.</p>
{stats((f"{n_ver} of {len(refs)}", "references confirmed"), (str(n_bad), "could not be confirmed"),
       ("1", "new regional source found"))}
<ul>
<li>One cited title was incomplete (Leray et al. 2013 — full title restored); the Deepor algae paper is
<strong>Baruah et al. 2020</strong>, not 2021.</li>
<li>Two regional papers (<em>Tropical Ecology</em> 2011, <em>Indian Journal of Fisheries</em> 2015) are not registered in
Crossref and could not be confirmed electronically — check them against the printed journals before citing.</li>
<li>While checking, a directly relevant microscopy survey turned up: Sharma (2010), <em>Rotifer communities of
Deepor Beel</em> — used in the next step.</li>
</ul>
{specialist(script("scripts/14_verify_references.py"),
            files(f"{REF}/references_formatted.md", f"{REF}/references_verified.tsv"))}
"""))

steps.append(("microscopy", "Step 15", "Does DNA agree with the microscope?", f"""
<p class='plain'><span>In plain words</span>Before DNA methods, biologists counted plankton under the microscope. Two such
surveys exist for Deepor Beel: rotifers in 2002–03 and algae published in 2020. If DNA is reliable, it should find much of
what they found — and may find more.</p>
<p><strong>Algae — strong agreement on what matters.</strong> The microscopists found desmids, above all
<em>Cosmarium</em>, to be the richest group in Deepor; DNA independently picks out the same desmids
(<em>{", ".join(desmids_both[:5])}</em>…). In all, {len(alg_both)} algal genera are shared, and DNA adds {alg_dna_only} genera the
survey did not list. Of the genera seen only under the microscope, {alg_blind} are cyanobacteria or euglenoids, which
this DNA marker cannot see or sees poorly — cyanobacteria are bacteria and have no 18S gene at all.</p>
<p><strong>Rotifers — agreement at the genus level.</strong> Of the five rotifer genera the microscopists found most important,
DNA detects four (<em>Brachionus</em>, <em>Keratella</em>, <em>Asplanchna</em> and, provisionally, <em>Lecane</em>). At species level only
<em>Keratella tropica</em> and <em>Polyarthra vulgaris</em> are confirmed, because most rotifer species have no DNA in the reference
libraries yet — the same gap seen in Steps 7 and 10.</p>
{fig("15_microscopy.png", "Taxa recorded by microscopy in Deepor Beel, and how many of them the DNA data also detected.")}
<p class='src'>The surveys were made in other years and seasons; only presence is compared. Historical water quality from the
2002–03 survey (pH ≈ 6.9, dissolved oxygen ≈ 7 mg/l, conductivity ≈ 98 µS/cm) is context only, not a measurement of these
samples.</p>
{specialist(
    "<p>Literature taxa in <a href='" + BLOB + "/scripts/literature_deepor.tsv'>scripts/literature_deepor.tsv</a>: rotifer "
    "families, genera and species from Sharma (2010, Table 3); algal genera from the species accounts of Baruah et "
    "al. (2020). DNA detections in Deepor (W2) only.</p>",
    script("scripts/15_microscopy_comparison.R"),
    table(f"{MI}/comparison_summary.tsv", {"also_by_DNA_named": "DNA (named)", "also_by_DNA_provisional": "DNA (provisional)",
                                         "DNA_only": "DNA only"}),
    table(f"{MI}/rotifers_microscopy_vs_DNA.tsv", {"dna_detection": "DNA"}),
    files(f"{MI}/algae_genera_microscopy_vs_DNA.tsv", f"{MI}/rotifer_genera_DNA_Deepor.tsv"))}
"""))

steps.append(("findings", "In summary", "What the data tells us", f"""
<div class='finding'><h4>Two very different microscopic worlds</h4>
<p>Chandubi is an algae-and-grazer lake: green algae, diatoms, protozoa and rotifers. Deepor is richer in kinds but leans
towards fungi, water moulds, desmids and small worms. By 18S the lakes share only {ovl[('18S','ASV')]['pct_shared']}% of
their DNA types.</p></div>
<div class='finding'><h4>Rotifers rule the zooplankton</h4>
<p>About {float(cgrp['Rotifers']['W1']):.0f}% (Chandubi) and {float(cgrp['Rotifers']['W2']):.0f}% (Deepor) of animal (COI) reads are
rotifers, many of them species not yet in any DNA library. Copepods (<em>Mesocyclops</em>, <em>Eucyclops</em>,
<em>Microcyclops</em>) are present; water fleas were not detected.</p></div>
<div class='finding'><h4>Two barcodes are better than one</h4>
<p>Most named animal genera were seen by only one of the two barcodes — neither alone gives the full picture.</p></div>
<div class='finding'><h4>An abundant, unknown organism</h4>
<p>The most common COI signature in both lakes matches nothing on record above ~72% at DNA level; even its protein sits
between a nematode and stramenopile algae. It is a genuine unknown — a candidate for closer study.</p></div>
<div class='finding'><h4>A nutrient-rich signal in both lakes</h4>
<p>The rotifer index QB/T is about {qbt['W1']['QBT']} in Chandubi and {qbt['W2']['QBT']} in Deepor — well above the threshold of 2
for nutrient-rich water (provisional, as some genus names rest on distant matches).</p></div>
<div class='finding'><h4>Shared zooplankton, different microbes</h4>
<p>By COI, {cco['shared_asvs']} of {cco['total_asvs']} animal signatures occur in <em>both</em> lakes at similar levels, while the
algae, protists and fungi (18S) differ sharply. The sequencing lab has confirmed that the samples were handled correctly, so
this is treated as a real pattern: the two floodplain lakes appear to draw on the same regional pool of rotifers, while
their microscopic producers and decomposers reflect each lake’s own conditions.</p></div>
<div class='finding'><h4>DNA agrees with the microscope</h4>
<p>In Deepor, DNA recovers the desmids that microscopists found dominant and four of the five key rotifer genera — and adds
genera the surveys did not list.</p></div>
<div class='finding'><h4>Cautions</h4>
<p>One water sample per lake: differences describe these two samples and cannot be tested statistically. Read counts
reflect DNA, not the number or weight of organisms. Traces of fish and mammal DNA in Deepor are too few to interpret.</p></div>
"""))

steps.append(("next", "Still to do", "Before submission", """
<ul>
<li><strong>Sampling coordinates</strong> — the only value still missing, in the manuscript (Study area) and the SRA BioSample sheet.</li>
<li><strong>NCBI SRA upload</strong> — by the authors, using the prepared sheets; then add the BioProject accession to the
Data availability statement.</li>
<li><strong>Author details</strong> — co-authors, ORCID, acknowledgements, funding and competing-interest statements on the
title page and declarations (marked in brackets).</li>
<li><strong>Replication</strong> — more samples per lake (or another season) would allow statistical comparison in a follow-up study.</li>
</ul>
"""))
timeline = "".join(
    f"<li class='node' id='{sid}'><div class='dot'></div><div class='card'>"
    f"<p class='kicker'>{esc(k)}</p><h2>{esc(t)}</h2>{body}</div></li>"
    for sid, k, t, body in steps)
toc = "".join(f"<a href='#{sid}'>{esc(t)}</a>" for sid, k, t, _ in steps)

glossary = [
    ("eDNA", "Environmental DNA — genetic material organisms leave in water, soil or air."),
    ("Barcode gene", "A short gene that differs between species, used like a product barcode to tell them apart."),
    ("Read", "One stretch of DNA letters produced by the sequencer."),
    ("Primer", "A short starter DNA piece used to copy the barcode; removed before analysis."),
    ("ASV", "Amplicon sequence variant — one exact, unique DNA signature, roughly one kind of organism."),
    ("Chimera", "An artificial sequence accidentally stitched from two organisms during copying."),
    ("Rarefaction", "A check of whether sampling more would have found many more signatures."),
    ("Reference library", "A collection of DNA sequences from organisms that experts have identified, used to name new sequences."),
    ("% identity", "How many DNA letters two sequences share; 97–100% usually means the same species."),
    ("Effective number of types", "Diversity expressed as the number of equally common types that would give the same diversity."),
    ("Indicator organism", "A species whose presence or abundance signals something about water conditions, such as nutrient level."),
    ("BLAST / GenBank", "BLAST is a search tool; GenBank is the public archive of nearly all published DNA sequences."),
]
gloss = "".join(f"<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>" for a, b in glossary)

page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lake DNA Timeline</title>
<meta name="description" content="How raw DNA sequencing data from Chandubi Beel and Deepor Beel, Assam, was cleaned into a reliable picture of plankton life — step by step, in plain language.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#f7f5f0; --card:#ffffff; --fg:#22262a; --muted:#6b7177; --line:#e4e0d6; --accent:#2b6c8f;
  --accent-soft:#e6eff4; --warm:#c2662d; --warm-soft:#f8ece3; --code:#f3f1ec; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#141619; --card:#1c1f23; --fg:#e7e9eb; --muted:#9aa1a8;
  --line:#2d3237; --accent:#7fb6d6; --accent-soft:#1d2a33; --warm:#e09a6a; --warm-soft:#2e231c; --code:#16181b; }} }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:17px/1.7 Inter,-apple-system,"Segoe UI",Roboto,sans-serif; }}
a {{ color:var(--accent); }}
.wrap {{ max-width:860px; margin:0 auto; padding:0 16px; }}
header {{ padding:72px 0 40px; }}
.eyebrow {{ text-transform:uppercase; letter-spacing:.14em; font-size:.75rem; color:var(--muted); font-weight:600; margin:0 0 14px; }}
h1, h2, h4 {{ font-family:Fraunces,Georgia,serif; font-weight:600; letter-spacing:-.01em; }}
h1 {{ font-size:clamp(2rem,5vw,3rem); line-height:1.1; margin:0 0 18px; }}
.lede {{ font-size:1.15rem; color:var(--muted); max-width:640px; margin:0 0 28px; }}
.lakes {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:0 0 28px; }}
.lake {{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:18px 20px; }}
.lake b {{ font-family:Fraunces,Georgia,serif; font-size:1.2rem; display:block; }}
.lake span {{ font-size:.9rem; color:var(--muted); }}
.lake.a {{ border-top:4px solid var(--accent); }} .lake.b {{ border-top:4px solid var(--warm); }}
.journey {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px; font-size:.88rem; color:var(--muted); margin:0 0 8px; }}
.journey span {{ background:var(--card); border:1px solid var(--line); border-radius:999px; padding:4px 12px; }}
.journey i {{ font-style:normal; opacity:.6; }}
.toc {{ display:flex; flex-wrap:wrap; gap:6px 16px; font-size:.88rem; padding:18px 0 0; border-top:1px solid var(--line); margin-top:28px; }}
.toc a {{ text-decoration:none; color:var(--muted); }} .toc a:hover {{ color:var(--accent); }}
ol.timeline {{ list-style:none; margin:24px 0 0; padding:0 0 0 34px; position:relative; }}
ol.timeline::before {{ content:""; position:absolute; left:9px; top:8px; bottom:8px; width:2px;
  background:linear-gradient(var(--accent), var(--warm)); opacity:.35; }}
.node {{ position:relative; margin:0 0 34px; scroll-margin-top:20px; }}
.dot {{ position:absolute; left:-34px; top:26px; width:20px; height:20px; border-radius:50%; background:var(--bg);
  border:3px solid var(--accent); }}
.node:nth-last-child(-n+2) .dot {{ border-color:var(--warm); }}
.card {{ background:var(--card); border:1px solid var(--line); border-radius:16px; padding:26px 28px; }}
.kicker {{ margin:0; text-transform:uppercase; letter-spacing:.12em; font-size:.72rem; font-weight:600; color:var(--accent); }}
.node:nth-last-child(-n+2) .kicker {{ color:var(--warm); }}
h2 {{ font-size:1.6rem; line-height:1.25; margin:4px 0 14px; }}
h4 {{ font-size:1.05rem; margin:0 0 4px; }}
p {{ margin:0 0 14px; }}
.plain {{ background:var(--accent-soft); border-radius:12px; padding:14px 18px; }}
.plain span {{ display:block; font-size:.72rem; text-transform:uppercase; letter-spacing:.12em; font-weight:600; color:var(--accent); margin-bottom:2px; }}
.pair {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin:6px 0 16px; }}
.pair > div {{ background:var(--bg); border-radius:12px; padding:14px 16px; }}
.pair p {{ margin:0; font-size:.94rem; }}
.stats {{ display:grid; grid-template-columns:repeat(3,1fr); gap:12px; margin:20px 0; }}
.stat {{ border-top:2px solid var(--line); padding-top:10px; }}
.stat b {{ display:block; font-family:Fraunces,Georgia,serif; font-size:1.7rem; line-height:1.15; font-weight:600; }}
.stat span {{ font-size:.85rem; color:var(--muted); }}
figure {{ margin:18px 0; }}
figure img {{ width:100%; height:auto; display:block; border-radius:10px; border:1px solid var(--line); background:#fff; }}
figcaption {{ font-size:.88rem; color:var(--muted); margin-top:8px; line-height:1.55; }}
details.spec {{ margin-top:18px; border-top:1px dashed var(--line); padding-top:12px; }}
details.spec > summary {{ cursor:pointer; font-size:.88rem; color:var(--muted); font-weight:500; list-style:none; }}
details.spec > summary::before {{ content:"+ "; color:var(--accent); font-weight:600; }}
details.spec[open] > summary::before {{ content:"− "; }}
.spec-body {{ font-size:.92rem; padding-top:10px; }}
details.code {{ border:1px solid var(--line); border-radius:10px; padding:8px 12px; margin:8px 0; }}
details.code summary {{ cursor:pointer; font-size:.88rem; }}
details.code summary span {{ font-weight:600; }}
code {{ font:.84em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
pre {{ background:var(--code); border-radius:8px; padding:14px; overflow:auto; font-size:.82rem; line-height:1.5; margin:8px 0; }}
.tbl {{ overflow-x:auto; margin:10px 0 0; }}
table {{ border-collapse:collapse; font-size:.84rem; width:100%; }}
th, td {{ text-align:left; padding:6px 10px; border-bottom:1px solid var(--line); white-space:nowrap; }}
th {{ font-weight:600; color:var(--muted); font-size:.78rem; }}
td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
.src {{ font-size:.78rem; margin:4px 0 12px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }} .grid figure {{ margin:6px 0; }}
.label {{ font-size:.75rem; text-transform:uppercase; letter-spacing:.1em; color:var(--muted); margin:16px 0 4px; font-weight:600; }}
.files {{ font-size:.85rem; padding-left:18px; margin:0; }}
.finding {{ border-left:3px solid var(--accent); padding:2px 0 2px 16px; margin:0 0 18px; }}
.finding p {{ margin:0; }}
.finding.warn {{ border-color:var(--warm); background:var(--warm-soft); border-radius:0 10px 10px 0; padding:12px 16px; }}
.glossary {{ padding:40px 0 10px; border-top:1px solid var(--line); margin-top:20px; }}
.glossary h2 {{ margin-top:0; }}
dl {{ display:grid; grid-template-columns:1fr 1fr; gap:14px 28px; margin:0; }}
dt {{ font-weight:600; }} dd {{ margin:0; color:var(--muted); font-size:.93rem; }}
footer {{ padding:30px 0 60px; font-size:.85rem; color:var(--muted); }}
@media (max-width:640px) {{
  body {{ font-size:16px; }} header {{ padding:44px 0 28px; }}
  .lakes, .pair, .grid, dl {{ grid-template-columns:1fr; }}
  .stats {{ grid-template-columns:1fr 1fr; }} .stat b {{ font-size:1.4rem; }}
  ol.timeline {{ padding-left:24px; }} .dot {{ left:-24px; width:16px; height:16px; }} ol.timeline::before {{ left:7px; }}
  .card {{ padding:20px 18px; }} h2 {{ font-size:1.35rem; }}
}}
</style></head>
<body>
<div class="wrap">
<header>
  <p class="eyebrow">Plankton DNA study · Assam, India</p>
  <h1>Reading the life of two lakes from a bottle of water</h1>
  <p class="lede">The tiny plants and animals drifting in a lake are too small and too many to count by eye.
  Instead, we read the DNA they leave in the water. This page follows that DNA from the sequencing machine to a
  picture of what lives in each lake and what it tells us — one step at a time.</p>
  <div class="lakes">
    <div class="lake a"><b>Chandubi Beel</b><span>Sample W1 · a natural lake at the foot of the Garo Hills, relatively undisturbed</span></div>
    <div class="lake b"><b>Deepor Beel</b><span>Sample W2 · a Ramsar wetland on the edge of Guwahati, under urban pressure</span></div>
  </div>
  <div class="journey"><span>Lake water</span><i>→</i><span>DNA</span><i>→</i><span>Sequencer</span><i>→</i>
    <span>Check</span><i>→</i><span>Trim</span><i>→</i><span>Remove typos</span><i>→</i><span>Remove fakes</span><i>→</i><span>Name</span><i>→</i><span>Look up unknowns</span><i>→</i><span>Diversity</span><i>→</i><span>Ecology</span><i>→</i><span>Proteins</span><i>→</i><span>Paper files</span><i>→</i><span>Microscopy check</span></div>
  <nav class="toc">{toc}</nav>
</header>
<main>
<ol class="timeline">{timeline}</ol>
<section class="glossary"><h2>Words used on this page</h2><dl>{gloss}</dl></section>
</main>
<footer>Scripts, results and raw data: <a href="{REPO}">github.com/Angsumi/Sahil_Metagenome</a> ·
Reproduce with <a href="{BLOB}/scripts/run_all.sh">run_all.sh</a> and <a href="{BLOB}/environment.yml">environment.yml</a> ·
Page built {date.today().isoformat()}.</footer>
</div>
</body></html>
"""
(DOCS / "index.html").write_text(page)
(DOCS / ".nojekyll").touch()
print(f"wrote {DOCS / 'index.html'}")
