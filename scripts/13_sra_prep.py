#!/usr/bin/env python3
"""Step 13 — Prepare an NCBI SRA submission: one BioSample per lake (MIMARKS survey, water
package) and one SRA run per marker x lake (4 runs, 8 FASTQ files). Raw files share names
across markers (W1_R1.fastq.gz ...), which SRA does not allow in one submission, so uniquely
named hard links are created in work/sra_upload/ for uploading.
Only the sampling coordinates are left for the authors (TO_FILL); the collection date is
recorded as "missing", an INSDC-accepted value."""
import csv
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/13_sra"
UPLOAD = ROOT / "work/sra_upload"
OUT.mkdir(parents=True, exist_ok=True)
UPLOAD.mkdir(parents=True, exist_ok=True)

sites = {
    "W1": {"folder": "Chandubi", "name": "Chandubi_Beel", "title": "Chandubi Beel lake water, eDNA",
           "geo": "India: Assam, Kamrup, Chandubi Beel"},
    "W2": {"folder": "Dipor Beel", "name": "Deepor_Beel", "title": "Deepor Beel (Ramsar site) lake water, eDNA",
           "geo": "India: Assam, Guwahati, Deepor Beel"},
}
markers = {
    "18S": {"desc": "18S rRNA V4 amplicon, primers E572F (CYGCGGTAATTCCAGCTC) / E1009R "
                    "(AYGGTATCTRWTCRTCTTYG); Illumina MiSeq 2x300 bp",
            "title": "18S rRNA V4 amplicon of lake water eDNA"},
    "COI": {"desc": "COI Leray fragment amplicon, primers mlCOIintF (GGWACWGGWTGAACWGTWTAYCCYCC) / "
                    "jgHCO2198 (TAIACYTCIGGRTGICCRAARAAYCA); Illumina MiSeq 2x300 bp",
            "title": "COI amplicon of lake water eDNA"},
}

biosample_cols = ["*sample_name", "sample_title", "bioproject_accession", "*organism", "*collection_date",
                  "*env_broad_scale", "*env_local_scale", "*env_medium", "*geo_loc_name", "*lat_lon", "description"]
with open(OUT / "biosample_MIMARKS_survey_water.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(biosample_cols)
    for sid, s in sites.items():
        w.writerow([s["name"], s["title"], "",
                    "freshwater metagenome", "missing",
                    "freshwater lake biome [ENVO:01000252]", "freshwater lake [ENVO:00000021]",
                    "lake water [ENVO:04000007]", s["geo"], "TO_FILL (decimal degrees, e.g. 26.12 N 91.66 E)",
                    f"Surface water sample {sid}; eDNA metabarcoding with 18S rRNA V4 and COI markers"])

sra_cols = ["sample_name", "library_ID", "title", "library_strategy", "library_source", "library_selection",
            "library_layout", "platform", "instrument_model", "design_description", "filetype",
            "filename", "filename2", "filename_md5", "filename2_md5"]


def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


with open(OUT / "sra_metadata.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(sra_cols)
    for m, mk in markers.items():
        for sid, s in sites.items():
            names = []
            for r in ("R1", "R2"):
                src = ROOT / "NEW" / m / s["folder"] / f"{sid}_{r}.fastq.gz"
                dst = UPLOAD / f"{m}_{s['name']}_{sid}_{r}.fastq.gz"
                if dst.exists():
                    dst.unlink()
                os.link(src, dst)
                names.append((dst.name, md5(dst)))
            w.writerow([s["name"], f"{m}_{s['name']}", f"{mk['title']}: {s['title'].split(',')[0]}",
                        "AMPLICON", "METAGENOMIC", "PCR", "paired", "ILLUMINA", "Illumina MiSeq",
                        mk["desc"], "fastq", names[0][0], names[1][0], names[0][1], names[1][1]])
print(f"wrote {OUT}/biosample_MIMARKS_survey_water.tsv, {OUT}/sra_metadata.tsv; files in {UPLOAD}")
