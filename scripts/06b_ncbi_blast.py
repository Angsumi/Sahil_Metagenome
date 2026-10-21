#!/usr/bin/env python3
"""Step 6b helper — BLAST a FASTA file against NCBI core_nt through the NCBI BLAST
URL API (submit, poll, fetch). Writes one tab-separated row per hit:
qseqid, accession, pident, align_len, qcov, evalue, taxid, sciname, kingdom, phylum, class.
Usage: 06b_ncbi_blast.py query.fasta out.tsv [max_hits] [--sensitive]
--sensitive uses blastn (word size 11) instead of megablast, for distant matches.
Appends kingdom, phylum and class of each hit from NCBI Taxonomy."""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
query, out = sys.argv[1], sys.argv[2]
max_hits = int(sys.argv[3]) if len(sys.argv) > 3 else 5
sensitive = "--sensitive" in sys.argv


def call(params, data=False):
    enc = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(URL, data=enc if data else None,
                                 headers={"User-Agent": "Sahil_Metagenome/1.0 (amplicon taxonomy)"})
    if not data:
        req.full_url = URL + "?" + enc.decode()
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


fasta = open(query).read()
qlen = {m.group(1): len(m.group(2).replace("\n", ""))
        for m in re.finditer(r">(\S+)[^\n]*\n([^>]*)", fasta)}

if sensitive:
    mode = {"PROGRAM": "blastn", "DATABASE": "core_nt", "MEGABLAST": "off", "WORD_SIZE": 11}
else:
    mode = {"PROGRAM": "blastn", "DATABASE": "core_nt", "MEGABLAST": "on"}
resp = call({"CMD": "Put", **mode,
             "QUERY": fasta, "HITLIST_SIZE": max_hits, "EXPECT": "1e-20",
             "EMAIL": "", "TOOL": "Sahil_Metagenome"}, data=True).decode()
rid = re.search(r"RID = (\S+)", resp).group(1)
wait = int(re.search(r"RTOE = (\d+)", resp).group(1))
print(f"RID {rid}, estimated {wait}s", file=sys.stderr)
time.sleep(max(wait, 30))
deadline = time.time() + 90 * 60  # give up after 90 minutes
while True:
    if time.time() > deadline:
        sys.exit(f"BLAST RID {rid} did not finish within 90 minutes")
    status = call({"CMD": "Get", "RID": rid, "FORMAT_OBJECT": "SearchInfo"}).decode()
    s = re.search(r"Status=(\w+)", status).group(1)
    print(f"{time.strftime('%H:%M')} status {s}", file=sys.stderr, flush=True)
    if s == "READY":
        break
    if s in ("FAILED", "UNKNOWN"):
        sys.exit(f"BLAST {s} for RID {rid}")
    time.sleep(60)

raw = call({"CMD": "Get", "RID": rid, "FORMAT_TYPE": "JSON2_S"})
doc = json.loads(raw)
rows = []
for rep in doc["BlastOutput2"]:
    search = rep["report"]["results"]["search"]
    q = search["query_title"].split()[0]
    for hit in search.get("hits", []):
        d = hit["description"][0]
        hsp = hit["hsps"][0]
        rows.append([q, d.get("accession", ""), round(100 * hsp["identity"] / hsp["align_len"], 2),
                     hsp["align_len"], round(100 * (hsp["query_to"] - hsp["query_from"] + 1) / qlen[q], 1),
                     hsp["evalue"], str(d.get("taxid", "")), d.get("sciname", "")])

# Higher taxonomy (phylum, class) for each hit, from NCBI Taxonomy via E-utilities
lineage = {}
taxids = sorted({r[6] for r in rows if r[6]})
for i in range(0, len(taxids), 100):
    xml = urllib.request.urlopen(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&id=" + ",".join(taxids[i:i + 100]),
        timeout=120).read().decode()
    for taxon in re.findall(r"<Taxon>\s*<TaxId>(\d+)</TaxId>(.*?)</LineageEx>", xml, re.S):
        tid, body = taxon
        ranks = dict((r, n) for n, r in re.findall(
            r"<ScientificName>([^<]+)</ScientificName>\s*<Rank>([^<]+)</Rank>", body))
        lineage[tid] = (ranks.get("kingdom", ranks.get("superkingdom", "")), ranks.get("phylum", ""),
                        ranks.get("class", ""))
    time.sleep(0.5)

with open(out, "w") as fh:
    for r in rows:
        fh.write("\t".join(map(str, r + list(lineage.get(r[6], ("", "", ""))))) + "\n")
print(f"wrote {out}", file=sys.stderr)
