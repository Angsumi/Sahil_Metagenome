# Step 3 — DADA2: filter/trim, learn errors, denoise both sites JOINTLY (pool = TRUE),
# merge pairs, remove chimeras. One run per marker so ASVs are comparable across sites.
# Usage: Rscript scripts/03_dada2.R <marker> <truncF> <truncR> <maxEE_F> <maxEE_R>
suppressPackageStartupMessages({ library(dada2); library(ggplot2); library(data.table) })

args <- commandArgs(trailingOnly = TRUE)
marker <- args[1]
truncLen <- as.integer(args[2:3])
maxEE <- as.numeric(args[4:5])
set.seed(2026)

inDir <- file.path("work/02_trimmed", marker)
filtDir <- file.path("work/03_filtered", marker)
out <- file.path("results/03_dada2", marker)
dir.create(filtDir, recursive = TRUE, showWarnings = FALSE)
dir.create(out, recursive = TRUE, showWarnings = FALSE)

fnF <- sort(list.files(inDir, "_R1.fastq.gz$", full.names = TRUE))
fnR <- sort(list.files(inDir, "_R2.fastq.gz$", full.names = TRUE))
samples <- sub("_R1.fastq.gz$", "", basename(fnF))
filtF <- file.path(filtDir, paste0(samples, "_F.fastq.gz"))
filtR <- file.path(filtDir, paste0(samples, "_R.fastq.gz"))
names(filtF) <- names(filtR) <- samples

# 3a. Quality filtering
filt <- filterAndTrim(fnF, filtF, fnR, filtR, truncLen = truncLen, maxEE = maxEE,
                      maxN = 0, truncQ = 2, rm.phix = TRUE, compress = TRUE, multithread = TRUE)

# 3b. Error models
errF <- learnErrors(filtF, multithread = TRUE, randomize = TRUE, verbose = FALSE)
errR <- learnErrors(filtR, multithread = TRUE, randomize = TRUE, verbose = FALSE)
for (d in list(list(errF, "R1"), list(errR, "R2"))) {
  p <- plotErrors(d[[1]], nominalQ = TRUE) +
    ggtitle(sprintf("%s %s — learned error rates (points) vs fitted model (black line)", marker, d[[2]]))
  ggsave(sprintf("docs/img/03_errors_%s_%s.png", marker, d[[2]]), p, width = 9, height = 7, dpi = 110)
}

# 3c. Joint denoising of both sites
dadaF <- dada(filtF, err = errF, pool = TRUE, multithread = TRUE, verbose = FALSE)
dadaR <- dada(filtR, err = errR, pool = TRUE, multithread = TRUE, verbose = FALSE)

# 3d. Merge pairs, build table, remove chimeras
mergers <- mergePairs(dadaF, filtF, dadaR, filtR, minOverlap = 12, maxMismatch = 0)
seqtab <- makeSequenceTable(mergers)
nochim <- removeBimeraDenovo(seqtab, method = "consensus", multithread = TRUE)

# 3e. Outputs: ASV table, ASV FASTA, length table, read tracking
getN <- function(x) sum(getUniques(x))
track <- data.table(marker = marker, sample = samples,
                    input = filt[, 1], filtered = filt[, 2],
                    denoisedF = sapply(dadaF, getN), denoisedR = sapply(dadaR, getN),
                    merged = sapply(mergers, getN), nonchim = rowSums(nochim))
fwrite(track, file.path(out, "track.tsv"), sep = "\t")

asv_seqs <- colnames(nochim)
asv_ids <- sprintf("%s_ASV%04d", marker, seq_along(asv_seqs))
counts <- data.table(asv = asv_ids, t(nochim))
setnames(counts, c("asv", rownames(nochim)))
counts[, length := nchar(asv_seqs)][, sequence := asv_seqs]
fwrite(counts, file.path(out, "asv_table.tsv"), sep = "\t")
writeLines(paste0(">", asv_ids, "\n", asv_seqs), file.path(out, "asv_seqs.fasta"))

lens <- data.table(length = nchar(colnames(seqtab)), reads = colSums(seqtab),
                   chimera = !colnames(seqtab) %in% asv_seqs)
fwrite(lens[, .(asvs = .N, reads = sum(reads)), by = .(length, chimera)][order(length)],
       file.path(out, "merged_lengths.tsv"), sep = "\t")

summary <- list(marker = marker, truncLen = truncLen, maxEE = maxEE,
                asvs_before_chimera = ncol(seqtab), asvs_final = ncol(nochim),
                chimeric_read_pct = round(100 * (1 - sum(nochim) / sum(seqtab)), 2))
jsonlite::write_json(summary, file.path(out, "summary.json"), auto_unbox = TRUE, pretty = TRUE)
print(track); str(summary)
