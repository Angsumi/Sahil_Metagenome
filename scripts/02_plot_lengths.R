# Step 2 — Plot read-retention after primer removal and trimmed read-length distribution.
suppressPackageStartupMessages({ library(ggplot2); library(data.table) })

s <- fread("results/02_primer_removal/cutadapt_summary.tsv")
s[, discarded := pairs_in - pairs_with_both_primers]
long <- melt(s, id.vars = c("marker", "sample"),
             measure.vars = c("pairs_with_both_primers", "discarded"),
             variable.name = "fate", value.name = "pairs")
long[, fate := factor(fate, levels = c("discarded", "pairs_with_both_primers"),
                      labels = c("discarded (primer not found)", "kept"))]
p1 <- ggplot(long, aes(sample, pairs, fill = fate)) +
  geom_col(width = 0.6) + facet_wrap(~marker) +
  scale_fill_manual(values = c("#d9d9d9", "#2b6c8f")) +
  scale_y_continuous(labels = scales::comma) +
  labs(x = NULL, y = "Read pairs", fill = NULL, title = "Read pairs kept after primer removal") +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom")
ggsave("docs/img/02_primer_retention.png", p1, width = 7, height = 4.5, dpi = 120)

l <- fread("results/02_primer_removal/trimmed_lengths.tsv")
p2 <- ggplot(l[length >= 150], aes(length, count, colour = sample)) +
  geom_line() + facet_grid(read ~ marker, scales = "free_y") +
  scale_y_log10(labels = scales::comma) +
  scale_colour_manual(values = c(W1 = "#2b6c8f", W2 = "#c2662d"),
                      labels = c(W1 = "Chandubi (W1)", W2 = "Deepor Beel (W2)")) +
  labs(x = "Read length after primer removal (bp)", y = "Reads (log scale)", colour = NULL,
       title = "Trimmed read-length distribution") +
  theme_minimal(base_size = 12) + theme(legend.position = "bottom")
ggsave("docs/img/02_trimmed_lengths.png", p2, width = 8, height = 5, dpi = 120)
