#!/usr/bin/env python3
"""Step 6 — Build the GitHub Pages site (docs/index.html) from the scripts, result
tables and figures produced by steps 1–5. Standard library only."""
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


def table(path, rename=None, number_cols=None):
    rows = list(csv.reader(open(ROOT / path), delimiter="\t"))
    head, body = rows[0], rows[1:]
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
    out.append(f"<p class='src'>Source: <a href='{BLOB}/{path}'>{esc(path)}</a></p>")
    return "".join(out)


def script(path):
    code = (ROOT / path).read_text()
    lines = code.count("\n") + 1
    return (f"<details><summary><code>{esc(path)}</code> · {lines} lines"
            f" · <a href='{BLOB}/{path}'>view on GitHub</a></summary>"
            f"<pre><code>{esc(code)}</code></pre></details>")


def fig(name, caption):
    return (f"<figure><a href='img/{name}'><img src='img/{name}' alt='{esc(caption)}' loading='lazy'></a>"
            f"<figcaption>{esc(caption)}</figcaption></figure>")


def files(*paths):
    items = "".join(f"<li><a href='{BLOB}/{p}'>{esc(p)}</a></li>" for p in paths)
    return f"<p class='label'>Output files</p><ul class='files'>{items}</ul>"


# ---- numbers used in prose ----
track = {(r["marker"], r["sample"]): r for r in
         csv.DictReader(open(ROOT / "results/05_summary/read_tracking.tsv"), delimiter="\t")}
asv = {r["marker"]: r for r in
       csv.DictReader(open(ROOT / "results/05_summary/asv_counts.tsv"), delimiter="\t")}
dada = {m: json.load(open(ROOT / f"results/03_dada2/{m}/summary.json")) for m in ("18S", "COI")}
frame = (ROOT / "results/04_curation/COI_frame.txt").read_text().strip()

# MultiQC report is served from docs/ so it opens in the browser
(DOCS / "reports").mkdir(parents=True, exist_ok=True)
shutil.copy(ROOT / "results/01_qc/multiqc/multiqc_raw.html", DOCS / "reports/multiqc_raw.html")

steps = []

steps.append(("qc", "1 · Raw read quality control", f"""
<p>Checks that the eight raw files are intact and describes them before anything is changed.
Checksums are compared against the vendor's <code>MD5SUM_Raw.txt</code>; FastQC/MultiQC report
per-file quality; DADA2 plots quality along the read, which sets the truncation lengths in step 3.</p>
<p class='label'>Script</p>{script("scripts/01_qc.sh")}{script("scripts/01_quality_profiles.R")}
<p class='label'>Result</p>
{table("results/01_qc/md5_check.tsv")}
{table("results/01_qc/read_stats.tsv", {"mean_len": "mean length", "gc_pct": "GC %", "mean_q": "mean Q"})}
<p>All eight files pass their checksums. Every file comes from a single MiSeq run
(<code>M04635:72:000000000-MDYKK</code>), 2 × 301 bp. Forward reads stay above Q30 almost to the end;
reverse reads drop below Q20 after ~250 cycles, so R2 is truncated harder.</p>
<p class='label'>Visualisation</p>
{fig("01_quality_18S.png", "18S — quality along the read. Green: mean; orange: median and quartiles.")}
{fig("01_quality_COI.png", "COI — quality along the read.")}
<p><a href='reports/multiqc_raw.html'>Open the full MultiQC report →</a></p>
"""))

steps.append(("primers", "2 · Primer removal (Cutadapt)", f"""
<p>Primer sequence is not biological signal and must be removed before denoising. Each read must
<em>begin</em> with its primer; pairs where either primer is missing are discarded as off-target.
Primers were identified from the reads themselves:</p>
<div class='tbl'><table><thead><tr><th>Marker</th><th>Forward</th><th>Reverse</th><th>Region</th></tr></thead><tbody>
<tr><td>18S</td><td>E572F <code>CYGCGGTAATTCCAGCTC</code></td><td>E1009R <code>AYGGTATCTRWTCRTCTTYG</code></td><td>V4, Comeau et al. 2011</td></tr>
<tr><td>COI</td><td>mlCOIintF <code>GGWACWGGWTGAACWGTWTAYCCYCC</code></td><td>jgHCO2198 <code>TANACYTCNGGRTGNCCRAARAAYCA</code></td><td>Leray fragment, Leray et al. 2013</td></tr>
</tbody></table></div>
<p class='label'>Script</p>{script("scripts/02_primer_removal.sh")}{script("scripts/02_plot_lengths.R")}
<p class='label'>Result</p>
{table("results/02_primer_removal/cutadapt_summary.tsv", {"pairs_in": "pairs in", "pairs_with_both_primers": "pairs with both primers", "pct_kept": "% kept"})}
<p>88–90 % of pairs carry both primers. After trimming, 18S reads are ~283/281 bp and COI reads ~275/275 bp.</p>
<p class='label'>Visualisation</p>
{fig("02_primer_retention.png", "Read pairs kept vs discarded at primer removal.")}
{fig("02_trimmed_lengths.png", "Length of reads after primer removal (log scale).")}
{files("results/02_primer_removal/cutadapt_summary.tsv", "results/02_primer_removal/trimmed_lengths.tsv")}
"""))

steps.append(("dada2", "3 · Denoising into ASVs (DADA2)", f"""
<p>Reads are quality-filtered, an error model is learned from the data, and true sequence variants
(ASVs) are separated from sequencing errors. <strong>Both sites are denoised together</strong>
(<code>pool = TRUE</code>), so the same organism gets the same ASV in both lakes and the sites can be
compared directly. Pairs are then merged and chimeras removed.</p>
<div class='tbl'><table><thead><tr><th>Parameter</th><th>18S</th><th>COI</th></tr></thead><tbody>
<tr><td>truncLen (R1, R2)</td><td>{dada['18S']['truncLen'][0]}, {dada['18S']['truncLen'][1]}</td><td>{dada['COI']['truncLen'][0]}, {dada['COI']['truncLen'][1]}</td></tr>
<tr><td>maxEE (R1, R2)</td><td>2, 4</td><td>2, 4</td></tr>
<tr><td>Expected amplicon (no primers)</td><td>~380–430 bp</td><td>313 bp</td></tr>
<tr><td>ASVs before → after chimera removal</td><td>{dada['18S']['asvs_before_chimera']} → {dada['18S']['asvs_final']}</td><td>{dada['COI']['asvs_before_chimera']} → {dada['COI']['asvs_final']}</td></tr>
<tr><td>Reads lost as chimeras</td><td>{dada['18S']['chimeric_read_pct']} %</td><td>{dada['COI']['chimeric_read_pct']} %</td></tr>
</tbody></table></div>
<p class='label'>Script</p>{script("scripts/03_dada2.R")}
<p class='label'>Result</p>
<h4>18S</h4>{table("results/03_dada2/18S/track.tsv")}
<h4>COI</h4>{table("results/03_dada2/COI/track.tsv")}
<p>Merging succeeded for 88–90 % (18S) and 98–99 % (COI) of filtered reads. Merged 18S ASVs cluster at
399–411 bp; COI ASVs at 313 bp (the standard Leray fragment) and 316 bp (one extra codon).</p>
<p class='label'>Visualisation</p>
<p>Error models: black lines (fitted model) should follow the points (observed error rates) and fall
as quality rises.</p>
<div class='grid'>
{fig("03_errors_18S_R1.png", "18S R1 error model")}{fig("03_errors_18S_R2.png", "18S R2 error model")}
{fig("03_errors_COI_R1.png", "COI R1 error model")}{fig("03_errors_COI_R2.png", "COI R2 error model")}
</div>
{files("results/03_dada2/18S/asv_table.tsv", "results/03_dada2/18S/asv_seqs.fasta",
       "results/03_dada2/COI/asv_table.tsv", "results/03_dada2/COI/asv_seqs.fasta")}
"""))

steps.append(("curation", "4 · ASV curation", f"""
<p>Removes ASVs that cannot be the targeted gene.</p>
<ul>
<li><strong>COI</strong> is protein-coding. A genuine ASV differs from 313 bp only by whole codons
and translates with no stop codon under the invertebrate mitochondrial code (NCBI table 5).
ASVs failing either test are likely pseudogenes (NUMTs) or artefacts. Detected {frame.lower()}.</li>
<li><strong>18S</strong> ASVs are kept within the expected V4 length window, 350–480 bp.</li>
</ul>
<p class='label'>Script</p>{script("scripts/04_asv_curation.R")}
<p class='label'>Result</p>
{table("results/04_curation/curation_summary.tsv", {"W1_reads": "Chandubi reads", "W2_reads": "Deepor reads"})}
<p>Curation removes few reads: 0.4 % for COI and 2.6 % for 18S (almost all short ASVs from Chandubi).</p>
<p class='label'>Visualisation</p>
{fig("04_curation.png", "Every ASV by length and abundance, coloured by curation outcome.")}
{files("results/04_curation/18S_asv_table_curated.tsv", "results/04_curation/18S_asv_seqs_curated.fasta",
       "results/04_curation/COI_asv_table_curated.tsv", "results/04_curation/COI_asv_seqs_curated.fasta",
       "results/04_curation/COI_frame_check.tsv")}
"""))

c18, cco = asv["18S"], asv["COI"]
steps.append(("summary", "5 · Processing summary", f"""
<p>Follows every read from raw file to curated ASV table, counts ASVs per site, and checks with
rarefaction whether sequencing depth was enough.</p>
<p class='label'>Script</p>{script("scripts/05_summary.R")}
<p class='label'>Result</p>
{table("results/05_summary/read_tracking.tsv", {"primers_found": "primers found", "nonchim": "non-chimeric", "pct_retained": "% of raw retained"})}
{table("results/05_summary/asv_counts.tsv", {"W1_asvs": "Chandubi ASVs", "W2_asvs": "Deepor ASVs", "shared_asvs": "shared", "total_asvs": "total", "shared_reads_pct_W1": "% Chandubi reads in shared ASVs", "shared_reads_pct_W2": "% Deepor reads in shared ASVs", "bray_curtis": "Bray–Curtis", "jaccard": "Jaccard"})}
<p class='label'>Visualisation</p>
{fig("05_read_tracking.png", "Reads remaining after each step.")}
{fig("05_rarefaction.png", "Rarefaction curves for curated ASVs.")}
{fig("05_asv_counts.png", "ASVs per site and shared between sites.")}
<div class='note'><p><strong>Observations.</strong></p><ul>
<li>53–57 % (18S) and 70–72 % (COI) of raw read pairs reach the final table, against ~40 % in the vendor's COI processing.</li>
<li>All four rarefaction curves flatten: sequencing depth was sufficient for both markers at both sites.</li>
<li>With joint denoising, <strong>{cco['shared_asvs']} of {cco['total_asvs']} COI ASVs occur in both lakes</strong>
(vendor table: 2 of 272), confirming that the vendor's near-zero overlap was an artefact of denoising the samples separately.</li>
<li><strong>The two markers disagree on how similar the lakes are.</strong> COI: Bray–Curtis {cco['bray_curtis']},
shared ASVs at similar abundance in both lakes. 18S: Bray–Curtis {c18['bray_curtis']}, only {c18['shared_asvs']} shared ASVs.
The COI overlap does not look like tag-jumping (that leaves a trace count on one side, not matched abundances).
It may be a genuinely shared zooplankton pool, or the COI libraries may share template DNA; without
extraction/PCR blanks this cannot be told apart. Worth raising with the sequencing provider.</li>
<li>One sample per lake: these are descriptions, not tested differences.</li>
</ul></div>
{files("results/05_summary/read_tracking.tsv", "results/05_summary/asv_counts.tsv")}
"""))

nav = "".join(f"<li><a href='#{sid}'>{esc(title)}</a></li>" for sid, title, _ in steps)
sections = "".join(f"<section id='{sid}'><h2>{esc(title)}</h2>{body}</section>" for sid, title, body in steps)

page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sahil Metagenome — Processing</title>
<meta name="description" content="18S and COI amplicon processing for Chandubi Beel and Deepor Beel, Assam: scripts, results and figures for each step.">
<style>
:root {{ --bg:#fdfdfc; --fg:#1d1d1f; --muted:#6b6b70; --line:#e6e6e3; --accent:#2b6c8f; --code:#f4f4f2; --note:#f3f7fa; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#161618; --fg:#e8e8ea; --muted:#9a9aa0; --line:#2c2c30; --accent:#7fb6d6; --code:#1f1f22; --note:#1b2329; }}
  figure img {{ background:#fff; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif; }}
main {{ max-width:880px; margin:0 auto; padding:48px 16px 96px; }}
h1 {{ font-size:1.9rem; line-height:1.2; margin:0 0 8px; letter-spacing:-0.01em; }}
h2 {{ font-size:1.35rem; margin:0 0 12px; padding-top:8px; }}
h4 {{ margin:18px 0 6px; font-size:0.95rem; color:var(--muted); }}
section {{ border-top:1px solid var(--line); padding:36px 0 8px; margin-top:28px; }}
a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
.lede {{ color:var(--muted); margin:0 0 20px; }}
.meta {{ font-size:0.88rem; color:var(--muted); }}
.label {{ text-transform:uppercase; font-size:0.72rem; letter-spacing:0.08em; color:var(--muted); margin:26px 0 6px; font-weight:600; }}
nav ol {{ list-style:none; padding-left:0; margin:12px 0; }} nav li {{ margin:2px 0; }}
code {{ font:0.86em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
pre {{ background:var(--code); border:1px solid var(--line); border-radius:6px; padding:14px; overflow:auto; font-size:0.85rem; line-height:1.5; margin:8px 0 0; }}
details {{ border:1px solid var(--line); border-radius:6px; padding:8px 12px; margin:6px 0; }}
details[open] {{ padding-bottom:12px; }} summary {{ cursor:pointer; font-size:0.92rem; }}
.tbl {{ overflow-x:auto; margin:10px 0 2px; }}
table {{ border-collapse:collapse; font-size:0.88rem; width:100%; }}
th, td {{ text-align:left; padding:6px 10px; border-bottom:1px solid var(--line); white-space:nowrap; }}
th {{ font-weight:600; color:var(--muted); font-size:0.8rem; }}
td.n {{ text-align:right; font-variant-numeric:tabular-nums; }}
.src {{ font-size:0.78rem; color:var(--muted); margin:2px 0 14px; }}
figure {{ margin:16px 0; }} figure img {{ max-width:100%; height:auto; border:1px solid var(--line); border-radius:4px; display:block; }}
figcaption {{ font-size:0.85rem; color:var(--muted); margin-top:6px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }} .grid figure {{ margin:0; }}
@media (max-width:640px) {{ .grid {{ grid-template-columns:1fr; }} main {{ padding-top:28px; }} }}
.files {{ font-size:0.88rem; padding-left:20px; margin:4px 0; }}
.note {{ background:var(--note); border-left:3px solid var(--accent); padding:4px 16px; border-radius:4px; margin:20px 0; }}
footer {{ border-top:1px solid var(--line); margin-top:40px; padding-top:16px; font-size:0.85rem; color:var(--muted); }}
</style></head>
<body><main>
<h1>Plankton metabarcoding — read processing</h1>
<p class="lede">Raw 18S rRNA (V4) and COI amplicon reads from <strong>Chandubi Beel (W1)</strong> and
<strong>Deepor Beel (W2)</strong>, Assam, processed from FASTQ to curated ASV tables.
Each step lists its script, its result and its figures.</p>
<p class="meta">Illumina MiSeq 2 × 301 bp · 2 markers × 2 sites · one sample per site ·
<a href="{REPO}">GitHub repository</a> · <a href="{BLOB}/environment.yml">environment.yml</a> ·
<a href="{BLOB}/scripts/run_all.sh">run_all.sh</a></p>
<nav><ol>{nav}</ol></nav>
{sections}
<footer>Built {date.today().isoformat()} by <code>scripts/06_build_site.py</code>.
Next stage (not yet run): taxonomic assignment — 18S against PR2, COI against MIDORI2/BOLD.</footer>
</main></body></html>
"""
(DOCS / "index.html").write_text(page)
(DOCS / ".nojekyll").touch()
print(f"wrote {DOCS / 'index.html'}")
