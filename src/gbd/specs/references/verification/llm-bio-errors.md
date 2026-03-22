# Known LLM Bioinformatics Failure Modes

> This catalog documents systematic failure patterns of LLMs in bioinformatics research.
> The verifier and plan-checker cross-reference against these patterns.

## Critical Errors (High Frequency)

### E001: Genome Build Mismatch
**Pattern**: Mixing coordinates from different genome builds (hg19 vs hg38) without liftover.
**Example**: Using hg19 variant positions with an hg38 reference genome, producing silent misalignment.
**Guard**: Lock reference genome version in conventions. Verify all input files use the same build. Use liftOver/CrossMap when mixing builds is unavoidable.

### E002: Missing Multiple Testing Correction
**Pattern**: Reporting raw p-values from genome-wide tests as significant without FDR correction.
**Example**: Claiming 500 differentially expressed genes at p < 0.05 from 20,000 tests (expect 1,000 by chance).
**Guard**: Always apply BH or similar correction. Report both raw and adjusted p-values. Lock correction method in conventions.

### E003: Pseudoreplication
**Pattern**: Treating technical replicates as biological replicates, inflating sample size.
**Example**: Reporting n=12 when there are 4 biological samples each with 3 technical replicates.
**Guard**: Explicitly distinguish biological from technical replicates. Aggregate technical replicates before statistical testing.

### E004: Wrong Strandedness in RNA-seq
**Pattern**: Using unstranded counting for stranded libraries or vice versa, losing ~50% of reads or double-counting.
**Example**: Running featureCounts without -s flag on a stranded dUTP library.
**Guard**: Check library prep protocol. Verify strandedness with infer_experiment.py (RSeQC) before quantification.

### E005: Annotation Version Mismatch
**Pattern**: Using gene IDs from one annotation version with a different version's GTF/GFF.
**Example**: Mapping Ensembl gene IDs from release 98 against a GENCODE v44 GTF, losing 5-10% of genes.
**Guard**: Lock annotation version in conventions. Verify gene ID format matches GTF.

## Serious Errors (Medium Frequency)

### E006: Ignoring Batch Effects
**Pattern**: Performing differential expression without accounting for batch/technical confounders.
**Example**: Finding "differentially expressed" genes that actually reflect sequencing lane differences.
**Guard**: Always run PCA colored by batch variables. Include batch as covariate or use ComBat/SVA.

### E007: Inappropriate Normalization
**Pattern**: Using TPM/RPKM for differential expression testing (these are not suitable for statistical tests).
**Example**: Running t-tests on TPM values instead of using DESeq2/edgeR's built-in normalization.
**Guard**: Use DESeq2 median-of-ratios or TMM for DE testing. Use TPM only for visualization/reporting.

### E008: Survivorship Bias in Filtering
**Pattern**: Filtering genes AFTER statistical testing, then claiming filtered set is significant.
**Example**: Removing lowly-expressed genes after DE analysis, biasing FDR estimates.
**Guard**: Filter before normalization and testing. Document filtering criteria in conventions.

### E009: Incorrect Variant Calling for Sample Type
**Pattern**: Using germline variant caller for somatic samples or vice versa.
**Example**: Running GATK HaplotypeCaller on tumor-normal pairs instead of Mutect2.
**Guard**: Match variant caller to sample type. Lock variant caller in conventions with rationale.

### E010: P-value Threshold Shopping
**Pattern**: Trying multiple thresholds and reporting only the one that gives "interesting" results.
**Example**: Using FDR < 0.1 for one comparison and FDR < 0.05 for another without pre-specification.
**Guard**: Pre-specify significance thresholds in conventions before any analysis.

## Moderate Errors (Common but Usually Caught)

### E011: Ignoring Library Composition Bias
**Pattern**: Not accounting for highly expressed genes consuming a large fraction of reads.
**Example**: In RNA-seq, a few highly expressed genes change between conditions, making all other genes appear differentially expressed.
**Guard**: Use proper normalization (DESeq2, TMM) that accounts for composition bias. Check MA plots for asymmetry.

### E012: Wrong Reference for Non-Model Organisms
**Pattern**: Using a closely related species' reference when a species-specific reference exists.
**Example**: Aligning chimpanzee reads to human reference without noting mapping bias.
**Guard**: Search NCBI/Ensembl for species-specific reference. Document reference choice rationale.

### E013: Forgetting to Sort/Index BAM Files
**Pattern**: Using unsorted BAM files with tools that require coordinate-sorted input.
**Example**: Running GATK HaplotypeCaller on name-sorted BAMs, producing cryptic errors or wrong results.
**Guard**: Always sort (samtools sort) and index (samtools index) BAM files. Verify with samtools quickcheck.

### E014: Confusing Gene-Level and Transcript-Level Analysis
**Pattern**: Making gene-level claims from transcript-level quantification without proper aggregation.
**Example**: Reporting transcript isoform counts as gene expression, double-counting shared exons.
**Guard**: Explicitly state the analysis level. Use tximport for transcript-to-gene aggregation.

### E015: Outdated Tool Versions with Known Bugs
**Pattern**: Using old tool versions with known critical bugs that affect results.
**Example**: Using STAR < 2.7.9 with known splice junction scoring bug, or old GATK with known variant calling errors.
**Guard**: Check tool changelogs for critical bug fixes. Pin to recent stable versions. Lock versions in conventions.

## How to Use This Catalog

1. **Plan-checker**: Before execution, identify tasks where specific errors are likely. Add explicit guards.
2. **Executor**: Consult relevant entries when performing work of that type. Follow guards.
3. **Verifier**: After execution, cross-reference results against applicable error patterns.
4. **Pattern library**: When a new error pattern is discovered, add it here.
