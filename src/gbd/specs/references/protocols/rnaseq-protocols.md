# RNA-seq Analysis Protocols

> Step-by-step methodology guides for RNA-seq bioinformatics analysis.

## Protocol: Bulk RNA-seq Differential Expression

### When to Use
Identifying genes differentially expressed between conditions from bulk RNA-seq data.

### Steps
1. **Quality control** — Run FASTQC on raw FASTQ files, aggregate with MultiQC
2. **Adapter trimming** — Trim adapters and low-quality bases (fastp or Trimmomatic)
3. **Alignment** — Align to reference genome with STAR (splice-aware aligner)
4. **Post-alignment QC** — Check mapping rate (>80%), duplicate rate, insert size, gene body coverage (RSeQC)
5. **Strandedness check** — Verify library strandedness with infer_experiment.py
6. **Quantification** — Count reads per gene with featureCounts (with correct -s strandedness flag)
7. **Filtering** — Remove lowly-expressed genes (e.g., CPM > 1 in >= N samples)
8. **Normalization** — DESeq2 median-of-ratios or edgeR TMM
9. **Exploratory analysis** — PCA, sample clustering, check for outliers and batch effects
10. **Differential expression** — DESeq2 or edgeR with appropriate design matrix
11. **Multiple testing correction** — Benjamini-Hochberg FDR
12. **Results visualization** — MA plot, volcano plot, heatmap of top genes
13. **Gene set enrichment** — GSEA, g:Profiler, or clusterProfiler for pathway analysis

### Common LLM Pitfalls
- Wrong strandedness flag in featureCounts (E004)
- Using TPM for DE testing instead of raw counts (E007)
- Pseudoreplication of technical replicates (E003)
- Filtering after statistical testing (E008)

---

## Protocol: Single-Cell RNA-seq Analysis

### When to Use
Analyzing gene expression at single-cell resolution (10x Genomics, Drop-seq, Smart-seq2).

### Steps
1. **Raw data processing** — Cell Ranger (10x) or STARsolo for demultiplexing and alignment
2. **Quality control** — Filter cells by nUMI, nGenes, mitochondrial %, doublet detection (Scrublet, DoubletFinder)
3. **Normalization** — SCTransform (Seurat) or scran pooling normalization
4. **Feature selection** — Identify highly variable genes (HVGs)
5. **Dimensionality reduction** — PCA, then UMAP/t-SNE for visualization
6. **Clustering** — Graph-based clustering (Leiden, Louvain)
7. **Cluster annotation** — Marker genes, reference-based annotation (SingleR, Azimuth)
8. **Differential expression** — Wilcoxon rank-sum, MAST, or pseudobulk (recommended for multi-sample)
9. **Trajectory analysis** — Monocle3, Slingshot (if developmental trajectory expected)
10. **Cell-cell communication** — CellChat, LIANA (if relevant)

### Common LLM Pitfalls
- Treating individual cells as independent replicates across samples (E003)
- Not accounting for doublets in analysis
- Over-clustering or under-clustering without biological validation
- Using bulk RNA-seq DE methods on single-cell data

---

## Protocol: Pseudo-alignment Quantification

### When to Use
Fast transcript-level quantification without traditional alignment (Salmon, Kallisto).

### Steps
1. **Build index** — Salmon or Kallisto index from transcriptome FASTA (not genome)
2. **Quantification** — Run Salmon quant or Kallisto quant per sample
3. **Import to R** — Use tximport to aggregate transcript-to-gene level
4. **Continue with standard DE pipeline** — DESeq2 or edgeR from tximport counts
5. **Transcript-level analysis** — DRIMSeq or DEXSeq for differential transcript usage

### Common LLM Pitfalls
- Using genome FASTA instead of transcriptome FASTA for index
- Confusing transcript-level and gene-level counts (E014)
- Not using tximport's bias correction features

---

## Protocol: Long-Read RNA-seq (ONT/PacBio)

### When to Use
Full-length transcript sequencing for isoform discovery and quantification.

### Steps
1. **Basecalling** — Dorado (ONT) or CCS (PacBio HiFi)
2. **Quality control** — NanoPlot, PycoQC for read quality and length distributions
3. **Alignment** — minimap2 with splice-aware preset (-ax splice)
4. **Isoform identification** — IsoQuant, FLAIR, or StringTie2 for novel isoform discovery
5. **Quantification** — Transcript-level counts from IsoQuant or Bambu
6. **Differential analysis** — DESeq2 at transcript level, DRIMSeq for differential usage
7. **Fusion detection** — JAFFAL for gene fusion identification (if relevant)

### Common LLM Pitfalls
- Using short-read aligners for long reads
- Not accounting for higher error rates in ONT reads
- Applying short-read QC thresholds to long-read data
