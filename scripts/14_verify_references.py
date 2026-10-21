#!/usr/bin/env python3
"""Step 14 — Verify every reference cited in the draft manuscript and the Methods against
Crossref. For references with a DOI: fetch the record and compare title, first author and year
with what we cite. For references without a DOI: search Crossref by title and report the best
match. Writes results/14_references/references_verified.tsv and a formatted reference list built
from the Crossref records (not from our own notes)."""
import csv
import difflib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/14_references"
OUT.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "Sahil_Metagenome/1.0 (reference check; https://github.com/Angsumi/Sahil_Metagenome)"}

# (key, cited first author, cited year, cited title, DOI or "")
REFS = [
    ("Buchfink2021", "Buchfink", 2021, "Sensitive protein alignments at tree-of-life scale using DIAMOND", "10.1038/s41592-021-01101-x"),
    ("Callahan2016", "Callahan", 2016, "DADA2: High-resolution sample inference from Illumina amplicon data", "10.1038/nmeth.3869"),
    ("Chen2025", "Chen", 2025, "Advancing aquatic biodiversity assessments of invertebrates using eDNA metabarcoding: a systematic evaluation of primers for marine and freshwater communities", "10.1111/2041-210X.70152"),
    ("Comeau2011", "Comeau", 2011, "Arctic Ocean microbial community structure before and after the 2007 record sea ice minimum", "10.1371/journal.pone.0027492"),
    ("Edgar2016", "Edgar", 2016, "SINTAX: a simple non-Bayesian taxonomy classifier for 16S and ITS sequences", "10.1101/074161"),
    ("Ewels2016", "Ewels", 2016, "MultiQC: summarize analysis results for multiple tools and samples in a single report", "10.1093/bioinformatics/btw354"),
    ("Geller2013", "Geller", 2013, "Redesign of PCR primers for mitochondrial cytochrome c oxidase subunit I for marine invertebrates and application in all-taxa biotic surveys", "10.1111/1755-0998.12138"),
    ("Guillou2013", "Guillou", 2013, "The Protist Ribosomal Reference database (PR2): a catalog of unicellular eukaryote Small Sub-Unit rRNA sequences with curated taxonomy", "10.1093/nar/gks1160"),
    ("Jo2026", "Jo", 2026, "Seasonal and spatiotemporal dynamics of plankton communities using eDNA metabarcoding in Singal Reservoir", "10.1007/s00267-025-02357-1"),
    ("Lemonnier2025", "Lemonnier", 2025, "Comparison of metabarcoding and shotgun sequencing confirms the relevance of chloroplastic rRNA genes to assess community structure of lake phytoplankton", "10.1111/1755-0998.70077"),
    ("Leray2013", "Leray", 2013, "A new versatile primer set targeting a short fragment of the mitochondrial COI region for metabarcoding metazoan diversity", "10.1186/1742-9994-10-34"),
    ("Lin2023", "Lin", 2023, "Environmental DNA metabarcoding revealed the impacts of anthropogenic activities on phytoplankton diversity in Dianchi Lake and its three inflow rivers", "10.1002/ece3.10088"),
    ("Martin2011", "Martin", 2011, "Cutadapt removes adapter sequences from high-throughput sequencing reads", "10.14806/ej.17.1.200"),
    ("Porter2018", "Porter", 2018, "Automated high throughput animal CO1 metabarcode classification", "10.1038/s41598-018-22505-4"),
    ("Rognes2016", "Rognes", 2016, "VSEARCH: a versatile open source tool for metagenomics", "10.7717/peerj.2584"),
    ("Sahu2025", "Sahu", 2025, "Environmental DNA (eDNA): an eco-friendly approach for conservation of Indian freshwater diversity—a review", "10.1007/s11356-025-36202-z"),
    ("Shen2016", "Shen", 2016, "SeqKit: a cross-platform and ultrafast toolkit for FASTA/Q file manipulation", "10.1371/journal.pone.0163962"),
    ("Sildever2021", "Sildever", 2021, "Plankton biodiversity and species co-occurrence based on environmental DNA – a multiple marker study", "10.3897/mbmg.5.72371"),
    ("Sladecek1983", "Sládeček", 1983, "Rotifers as indicators of water quality", "10.1007/BF00027429"),
    ("Stefanni2018", "Stefanni", 2018, "Multi-marker metabarcoding approach to study mesozooplankton at basin scale", "10.1038/s41598-018-30157-7"),
    ("Zhang2018", "Zhang", 2018, "Metabarcoding using multiplexed markers increases species detection in complex zooplankton communities", "10.1111/eva.12694"),
    ("Zhao2021", "Zhao", 2021, "DNA metabarcoding of zooplankton communities: species diversity and seasonal variation revealed by 18S rRNA and COI", "10.7717/peerj.11057"),
    # Regional, morphology-based studies (no DOI known): searched by title
    ("Deepor_zooplankton2011", "", 2011, "Zooplankton communities of Deepor Beel (a Ramsar site), Assam (N.E. India): ecology, richness and abundance", ""),
    ("Deepor_phytoplankton2015", "", 2015, "Phytoplankton diversity of Deepor beel, a Ramsar site and floodplain lake of the Brahmaputra basin, Assam", ""),
    ("Deepor_algae2021", "", 2021, "Algal diversity in Deepor Beel of Assam: a Ramsar site of North East India", ""),
    # Found while checking the regional references: microscopy survey of Deepor Beel rotifers
    ("Sharma2010", "Sharma", 2010, "Rotifer communities of Deepor Beel, Assam, India: richness, abundance and ecology", "10.11609/jott.o2411.1077-86"),
]


def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(3)
        except Exception:
            time.sleep(3)
    return None


def norm(t):
    t = re.sub(r"<[^>]+>", "", t or "")
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower())
    return re.sub(r"\s+", " ", t).strip()


def fmt(m, cited_title="", cited_year=None):
    authors = m.get("author", [])
    names = [f"{a.get('family', '')} {''.join(p[0] for p in re.split(r'[ -]', a.get('given', '')) if p)}".strip()
             for a in authors]
    au = ", ".join(names[:6]) + (" et al." if len(names) > 6 else "")
    year = (m.get("issued", {}).get("date-parts") or [[None]])[0][0]
    print_year = (m.get("published-print", {}).get("date-parts") or [[None]])[0][0]
    if cited_year and cited_year in (year, print_year):
        year = cited_year
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", (m.get("title") or [""])[0])).strip().strip('"')
    if cited_title and norm(cited_title).startswith(norm(title)) and len(cited_title) > len(title):
        title = cited_title  # Crossref holds a truncated title
    jour = (m.get("container-title") or [m.get("publisher", "")])[0]
    vol = m.get("volume", "")
    pages = m.get("page", "") or m.get("article-number", "")
    loc = f" {vol}" if vol else ""
    loc += f": {pages}" if pages else ""
    return f"{au} ({year}). {title}. {jour}{loc}. https://doi.org/{m['DOI']}"


rows, formatted, records = [], [], {}
for key, author, year, title, doi in REFS:
    if doi:
        msg = (get("https://api.crossref.org/works/" + urllib.parse.quote(doi)) or {}).get("message")
        if not msg:
            rows.append([key, doi, "DOI NOT FOUND", "", "", "", "", ""])
            continue
    else:
        q = urllib.parse.urlencode({"query.bibliographic": title, "rows": 1})
        items = ((get("https://api.crossref.org/works?" + q) or {}).get("message") or {}).get("items") or []
        msg = items[0] if items else None
        if not msg:
            rows.append([key, "", "NO MATCH IN CROSSREF", "", "", "", "", ""])
            continue
    ctitle = re.sub(r"<[^>]+>", "", (msg.get("title") or [""])[0])
    cyear = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
    cfirst = (msg.get("author") or [{}])[0].get("family", "")
    sim = difflib.SequenceMatcher(None, norm(title), norm(ctitle)).ratio()
    years = {(msg.get(k, {}).get("date-parts") or [[None]])[0][0] for k in ("issued", "published-print", "published-online")}
    nt, nc = norm(title).strip(), norm(ctitle).strip()
    issues, notes = [], []
    if sim < 0.9:
        if doi and nc and nt.startswith(nc):
            notes.append("Crossref stores a truncated title")
        elif doi and nt and nc.startswith(nt):
            notes.append("cited title is incomplete — use the full Crossref title")
        else:
            issues.append(f"title differs (similarity {sim:.2f})")
    if year not in years and any(y and abs(y - year) == 1 for y in years):
        notes.append(f"Crossref dates it {cyear}; online and print issue fall in different years")
    elif year not in years:
        issues.append(f"year {cyear} not {year}")
    elif cyear != year:
        notes.append(f"online {min(y for y in years if y)}, print {year}")
    if author and norm(cfirst) != norm(author):
        issues.append(f"first author {cfirst} not {author}")
    if doi:
        status = ("VERIFIED" + (f" ({'; '.join(notes)})" if notes else "")) if not issues else "CHECK: " + "; ".join(issues)
    else:
        status = (f"FOUND (no DOI given; year {cyear}): " if sim >= 0.9 else "NOT FOUND — best Crossref match is a different work: ") + \
                 f"similarity {sim:.2f}"
    rows.append([key, msg.get("DOI", ""), status, cfirst, cyear, ctitle,
                 (msg.get("container-title") or [""])[0], f"{sim:.2f}"])
    if status.startswith(("VERIFIED", "FOUND")):
        formatted.append((key, fmt(msg, title, year)))
        ctit = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", (msg.get("title") or [""])[0])).strip().strip('"')
        if norm(title).startswith(norm(ctit)) and len(title) > len(ctit):
            ctit = title
        pyear = (msg.get("published-print", {}).get("date-parts") or [[None]])[0][0]
        records[key] = {"authors": [{"family": a.get("family", a.get("name", "")), "given": a.get("given", "")}
                                    for a in msg.get("author", [])],
                        "year": year if year in (cyear, pyear) else cyear, "title": ctit,
                        "journal": (msg.get("container-title") or [msg.get("publisher", "")])[0],
                        "volume": msg.get("volume", ""), "issue": msg.get("issue", ""),
                        "pages": msg.get("page", "") or msg.get("article-number", ""), "doi": msg.get("DOI", "")}
    time.sleep(0.3)

json.dump(records, open(OUT / "references_records.json", "w"), indent=1, ensure_ascii=False)
with open(OUT / "references_verified.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(["key", "doi", "status", "crossref_first_author", "crossref_year", "crossref_title",
                "crossref_journal", "title_similarity"])
    w.writerows(rows)

with open(OUT / "references_formatted.md", "w") as fh:
    fh.write("# References (verified against Crossref)\n\n")
    fh.write("Built from Crossref records. Software without a paper (vegan) is cited as an R package.\n\n")
    for i, (_, f) in enumerate(sorted(formatted, key=lambda x: x[1].lower()), 1):
        fh.write(f"{i}. {f}\n")
    fh.write("\nOksanen J, Simpson GL, Blanchet FG, et al. vegan: Community Ecology Package. "
             "R package version 2.7-5. https://CRAN.R-project.org/package=vegan\n")
    unresolved = [r for r in rows if not r[2].startswith(("VERIFIED", "FOUND"))]
    if unresolved:
        fh.write("\n## Not verified — do not cite until checked against the original\n\n")
        for r in unresolved:
            fh.write(f"- {r[0]}: {r[2]}\n")
for r in rows:
    print(f"{r[0]:<26} {r[2]}")
