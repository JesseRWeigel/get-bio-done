# Get Bio Done

> An AI copilot for autonomous bioinformatics research — from raw sequencing data to analysis pipeline to publication.

**Inspired by [Get Physics Done](https://github.com/psi-oss/get-physics-done)** — the open-source AI copilot that autonomously conducts physics research. Get Bio Done adapts GPD's architecture for bioinformatics, genomics, and computational biology research.

## Vision

Bioinformatics pipelines are complex, multi-step workflows where parameter choices at each stage cascade downstream. Reference genome version, alignment parameters, variant calling thresholds, statistical corrections — changing any one can invalidate all subsequent analysis. GPD's convention-locking architecture is a natural fit.

Get Bio Done wraps LLM capabilities in a verification-first framework that:
- **Locks pipeline parameters** across phases (reference genome, annotation sources, statistical thresholds, tool versions)
- **Verifies reproducibility** — known-sample validation, p-value/FDR consistency, pipeline determinism
- **Decomposes research** into phases: data QC → preprocessing → alignment → analysis → statistical testing → visualization → paper writing
- **Follows established best practices** — GATK, DESeq2, Seurat, Scanpy, etc.

## Architecture

Adapted from GPD's three-layer design:

### Layer 1 — Core Library (Python)
State management, phase lifecycle, git operations, convention locks, verification kernel.

### Layer 2 — MCP Servers
- `gbd-state` — Project state queries
- `gbd-conventions` — Pipeline parameter lock management
- `gbd-protocols` — Bioinformatics methodology protocols (WGS, RNA-seq, scRNA-seq, CHIP-seq, metagenomics, etc.)
- `gbd-patterns` — Cross-project learned patterns
- `gbd-verification` — Reproducibility and statistical validity checks
- `gbd-errors` — Known LLM bioinformatics failure modes

### Layer 3 — Agents & Commands
- `gbd-planner` — Pipeline design and task decomposition
- `gbd-executor` — Pipeline execution and analysis
- `gbd-verifier` — Results verification and reproducibility checking
- `gbd-researcher` — Database and literature research
- `gbd-statistician` — Statistical analysis and multiple testing correction
- `gbd-paper-writer` — Manuscript generation
- `gbd-referee` — Methodology and results review

## Convention Lock Fields

1. Reference genome version (GRCh38, GRCm39, T2T-CHM13, etc.)
2. Gene annotation source and version (GENCODE, RefSeq, Ensembl)
3. Aligner and version (BWA-MEM2, STAR, minimap2, etc.)
4. Variant caller and version (GATK HaplotypeCaller, DeepVariant, etc.)
5. Statistical significance threshold (alpha, FDR method)
6. Multiple testing correction method (Benjamini-Hochberg, Bonferroni, etc.)
7. Normalization method (TPM, RPKM, CPM, SCTransform, etc.)
8. Quality thresholds (MAPQ, base quality, read depth minimums)
9. Filtering criteria (variant quality, allele frequency, etc.)
10. Container/environment versions (Docker images, conda environments)

## Verification Framework

1. **Data quality** — FastQC metrics within acceptable ranges
2. **Alignment quality** — mapping rates, duplicate rates, coverage uniformity
3. **Known-sample validation** — control samples produce expected results
4. **Pipeline reproducibility** — same inputs produce same outputs
5. **Statistical validity** — appropriate tests, correct multiple testing correction
6. **FDR control** — false discovery rate properly controlled
7. **Batch effect assessment** — technical artifacts identified and corrected
8. **Biological plausibility** — results make biological sense (pathway enrichment, known markers)
9. **Sample identity** — no sample swaps (concordance checks)
10. **Version pinning** — all tool versions recorded and reproducible
11. **Literature comparison** — results consistent with published findings on similar data
12. **Visualization accuracy** — plots accurately represent underlying data

## Status

**Early development** — Scaffolding and initial design. Seeking domain expert contributors!

## Relationship to GPD

Convergence verification and reproducibility checking transfer from GPD. Bioinformatics adds pipeline reproducibility, statistical validity, and biological plausibility checks.

We plan to showcase this in the [GPD Discussion Show & Tell](https://github.com/psi-oss/get-physics-done/discussions) once operational.

## Contributing

We're looking for contributors with:
- Bioinformatics or computational biology research experience
- Experience with GATK, DESeq2, Seurat/Scanpy, or similar tools
- NGS data analysis pipeline experience
- Familiarity with GPD's architecture

See the [Issues](../../issues) for specific tasks.

## License

MIT
