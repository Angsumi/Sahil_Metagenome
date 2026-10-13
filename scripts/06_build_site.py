#!/usr/bin/env python3
"""Step 6 — Build the GitHub Pages site (docs/index.html) from the scripts, result
tables and figures produced by steps 1–5. The page is a plain-language timeline;
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

steps.append(("findings", "So far", "What the clean data already tells us", f"""
<div class='finding'><h4>Better use of the data</h4>
<p>{100*final_pairs/raw_pairs:.0f}% of the raw data reached the final tables (COI: 70–72%), compared with about 40% in the
lab’s original COI processing.</p></div>
<div class='finding'><h4>Algae &amp; protists: the lakes are very different</h4>
<p>By the 18S barcode, Chandubi and Deepor share only {c18['shared_asvs']} of {fmt(c18['total_asvs'])} signatures —
their microscopic communities are largely distinct.</p></div>
<div class='finding warn'><h4>Zooplankton: surprisingly similar — needs checking</h4>
<p>By the COI barcode, {cco['shared_asvs']} of {cco['total_asvs']} signatures appear in <em>both</em> lakes at similar levels.
The lab’s earlier report showed almost no overlap, but that came from processing the lakes separately. The remaining
question is whether the zooplankton truly are similar, or whether DNA crossed between the two samples in the lab.
No blank (control) samples were sequenced, so this can’t yet be told apart — it is a question for Eurofins.</p></div>
<div class='finding'><h4>A caution on comparisons</h4>
<p>There is one water sample per lake. Differences describe these two samples; they cannot yet be tested statistically.</p></div>
"""))

steps.append(("next", "Next", "Putting names to the signatures", """
<p>So far each signature is just a string of DNA letters. The next stage compares them against reference libraries of
known organisms — <strong>PR2</strong> for 18S and <strong>MIDORI2 / BOLD</strong> for COI — to name them
(“this is the rotifer <em>Keratella tropica</em>”). After that come diversity comparisons and the ecological story of the two lakes.</p>
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
  clean, trustworthy dataset — one step at a time.</p>
  <div class="lakes">
    <div class="lake a"><b>Chandubi Beel</b><span>Sample W1 · a natural lake at the foot of the Garo Hills, relatively undisturbed</span></div>
    <div class="lake b"><b>Deepor Beel</b><span>Sample W2 · a Ramsar wetland on the edge of Guwahati, under urban pressure</span></div>
  </div>
  <div class="journey"><span>Lake water</span><i>→</i><span>DNA</span><i>→</i><span>Sequencer</span><i>→</i>
    <span>Check</span><i>→</i><span>Trim</span><i>→</i><span>Remove typos</span><i>→</i><span>Remove fakes</span><i>→</i><span>Clean dataset</span></div>
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
