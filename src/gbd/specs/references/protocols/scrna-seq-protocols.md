# scRNA-seq Analysis Protocols

> Step-by-step methodology guides for single-cell RNA sequencing data analysis.

## Protocol: Quality Control and Filtering

### When to Use
Processing raw scRNA-seq count matrices to remove low-quality cells and uninformative genes before downstream analysis.

### Steps
1. **Compute per-cell QC metrics** — total UMI counts (library size), number of detected genes, percentage of mitochondrial reads (%MT), percentage of ribosomal reads
2. **Identify low-quality cells** — filter cells with: too few genes (<200–500, indicates empty droplets or debris), too many genes (>2500–5000 or >2 MADs above median, indicates doublets), high %MT (>10–20% depending on tissue, indicates damaged/dying cells)
3. **Use adaptive thresholds** — compute median ± N × MAD (median absolute deviations) for each metric; N = 3–5 is standard; log-transform counts before computing MAD
4. **Detect doublets computationally** — apply DoubletFinder, Scrublet, or scDblFinder; remove cells with high doublet scores (expected doublet rate ≈ 0.8% per 1000 cells loaded for 10x Chromium)
5. **Filter genes** — remove genes detected in fewer than 3–10 cells (uninformative); optionally remove mitochondrial and ribosomal genes before normalization if they dominate variance
6. **Assess batch effects** — if multiple samples/lanes, check for systematic differences in QC metrics; flag batches with anomalous distributions
7. **Document filtering decisions** — report the number of cells and genes before and after each filter, with the thresholds used
8. **Visualize** — violin plots of QC metrics per sample, scatter plots of genes vs counts colored by %MT

### Common LLM Pitfalls
- Using fixed thresholds across all experiments (thresholds should be data-driven; tissue type, chemistry version, and species all affect appropriate cutoffs)
- Filtering too aggressively on gene count (can remove rare cell types with genuinely low transcriptomic complexity, e.g., red blood cells, platelets)
- Ignoring doublets (doublets create artificial "intermediate" cell types that confound clustering)
- Not checking for ambient RNA contamination (SoupX, CellBender) before standard QC

---

## Protocol: Normalization (SCTransform and scran)

### When to Use
Removing technical variation (library size, capture efficiency) while preserving biological variation.

### Steps
1. **Choose the normalization method**:
   - **scran (deconvolution)**: pools cells into groups, computes pool-based size factors, deconvolves to cell-level factors; best for datasets with clearly distinct populations
   - **SCTransform (regularized negative binomial regression)**: fits a regularized NB model per gene, regresses out sequencing depth; best for datasets where standard normalization leaves residual depth effects
   - **Simple log-normalization**: divide by total counts, multiply by scale factor (10⁴), log1p transform; adequate for many analyses but less robust
2. **For scran**: pre-cluster cells (quickCluster) before computing size factors to avoid violating the assumption that most genes are not DE between pools
3. **For SCTransform**: use v2 (sctransform::vst, method = "glmGamPoi") for speed; the output is Pearson residuals (use for PCA/clustering) and corrected counts (use for DE testing)
4. **Regress out confounders** — optionally regress out %MT, cell cycle scores, or batch in the normalization step; but be cautious — regressing out real biological signals (e.g., cell cycle in cycling cell types) removes information
5. **Verify normalization** — plot library size vs first PC; a good normalization eliminates this correlation
6. **For integration across batches**: apply Harmony, Seurat CCA/RPCA, or scVI after normalization (see batch correction, not part of normalization per se)
7. **Select highly variable genes (HVGs)** — identify the top 2000–5000 HVGs for downstream analysis (PCA, clustering); use the variance-stabilized residuals (SCTransform) or the mean-variance trend (scran)
8. **Document** — report the normalization method, number of HVGs, and any confounders regressed out

### Common LLM Pitfalls
- Applying SCTransform and then log-normalizing on top (SCTransform output is already variance-stabilized; additional log transform is wrong)
- Using simple log-normalization for datasets with extreme depth variation (scran or SCTransform are more robust)
- Regressing out cell cycle without checking whether cell cycle is biologically relevant in the experiment
- Selecting too few HVGs (<1000) and losing rare cell type markers, or too many (>5000) and introducing noise

---

## Protocol: Clustering and Cell Type Annotation

### When to Use
Identifying cell populations and assigning biological identities to clusters.

### Steps
1. **Dimensionality reduction** — run PCA on HVGs; select the number of PCs using an elbow plot or molecular cross-validation (typically 10–50 PCs); verify with JackStraw or similar
2. **Build the neighbor graph** — k-nearest neighbor (KNN) or shared nearest neighbor (SNN) graph using the selected PCs; k = 20–30 is typical
3. **Community detection** — apply Leiden (preferred) or Louvain algorithm on the SNN graph; adjust the resolution parameter (0.1–2.0) to control cluster granularity
4. **Visualize** — UMAP or t-SNE for 2D visualization; color by cluster, sample, QC metrics, and known marker genes
5. **Find marker genes** — run differential expression (Wilcoxon rank-sum, MAST, or negative binomial) comparing each cluster to all others; report top markers ranked by fold-change and adjusted p-value
6. **Annotate cell types** — match marker gene profiles to known cell type signatures using: (a) manual curation from literature, (b) reference-based annotation (SingleR, Azimuth, CellTypist), (c) gene set enrichment against cell type databases (CellMarker, PanglaoDB)
7. **Validate annotations** — check for expected marker gene expression (e.g., CD3 for T cells, CD19 for B cells, EPCAM for epithelial); flag clusters without clear identity for further sub-clustering or manual review
8. **Iterate** — if clusters contain mixed populations, sub-cluster and re-annotate; if over-clustered, merge clusters with similar marker profiles and no biological distinction

### Common LLM Pitfalls
- Using UMAP coordinates for clustering (UMAP is for visualization only; clustering should use the PCA-based SNN graph)
- Setting resolution too high and splitting real populations into artificial sub-clusters (validate with marker genes, not just number of clusters)
- Annotating based on a single marker gene (use marker panels; single markers can be expressed across multiple cell types)
- Trusting automated annotation tools without manual verification (they can be wrong, especially for novel or tissue-specific cell types)

---

## Protocol: Differential Expression and Trajectory Analysis

### When to Use
Identifying genes that differ between conditions or along a developmental/differentiation trajectory.

### Steps
1. **For DE between conditions**: use pseudobulk aggregation — sum counts per cell type per sample, then apply bulk DE methods (DESeq2, edgeR); this properly accounts for biological replication and avoids inflated p-values from treating cells as independent observations
2. **For DE between clusters**: use Wilcoxon rank-sum (fast, nonparametric), MAST (accounts for dropout), or negative binomial regression; apply Bonferroni or BH correction for multiple testing
3. **Report practical significance** — filter by both adjusted p-value (< 0.05) and log2 fold-change (|log2FC| > 0.25–1.0); in scRNA-seq with thousands of cells, nearly everything is statistically significant
4. **For trajectory analysis**: select the trajectory inference method appropriate for the topology — Monocle 3 (complex trajectories, UMAP-based), Slingshot (bifurcating, stable), RNA velocity (scVelo, spliced/unspliced ratios)
5. **Infer pseudotime** — order cells along the trajectory from a defined root cell/state; validate that the ordering matches known biology (e.g., stem cells → progenitors → differentiated)
6. **Identify trajectory-associated genes** — fit expression as a function of pseudotime (GAMs, tradeSeq); identify genes that change significantly along the trajectory
7. **Validate with RNA velocity** — if spliced/unspliced data are available, compute RNA velocity to confirm the directionality of the trajectory
8. **Report and caveat** — trajectory analysis infers developmental ordering from a snapshot; it does not prove causality or temporal ordering without additional experimental validation (lineage tracing, time-course)

### Common LLM Pitfalls
- Running single-cell-level DE between conditions without pseudobulk aggregation (inflates sample size from n=3 biological replicates to n=thousands of cells, producing false positives)
- Reporting only p-values without fold-change thresholds (thousands of genes will be "significant" with enough cells)
- Treating pseudotime as real time (it is an ordering, not a temporal measurement)
- Using RNA velocity with polyA-captured data that has low unspliced read counts (need intronic reads; 10x 3' data works but can be noisy; SMART-seq2 does not capture unspliced RNA well)
