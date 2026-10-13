# Step 1d — DADA2 per-position quality profiles of the raw reads (R1 and R2, both sites).
suppressPackageStartupMessages({ library(dada2); library(ggplot2) })

for (marker in c("18S", "COI")) {
  files <- sort(list.files(file.path("NEW", marker), pattern = "fastq.gz$",
                           recursive = TRUE, full.names = TRUE))
  p <- plotQualityProfile(files, n = 50000) +
    ggtitle(sprintf("%s raw reads — per-position quality", marker)) +
    theme(plot.title = element_text(size = 12))
  ggsave(sprintf("docs/img/01_quality_%s.png", marker), p, width = 10, height = 7, dpi = 120)
}
