# Variant Calling Protocols

> Step-by-step methodology guides for DNA variant calling and analysis.

## Protocol: Germline Short Variant Discovery (WGS/WES)

### When to Use
Identifying SNPs and small indels from whole-genome or whole-exome sequencing.

### Steps
1. **Quality control** — FASTQC on raw reads, check adapter content and quality scores
2. **Trimming** — fastp or Trimmomatic for adapter removal and quality trimming
3. **Alignment** — BWA-MEM2 to reference genome (GRCh38)
4. **Post-alignment processing**:
   a. Sort by coordinate (samtools sort)
   b. Mark duplicates (GATK MarkDuplicates or samtools markdup)
   c. Base quality score recalibration (GATK BQSR with known sites)
5. **Variant calling** — GATK HaplotypeCaller in GVCF mode per sample
6. **Joint genotyping** — GATK GenomicsDBImport + GenotypeGVCFs for cohorts
7. **Variant filtering** — GATK VQSR (>30 samples) or CNN score filtering (<30 samples)
8. **Variant annotation** — VEP, SnpEff, or ANNOVAR for functional annotation
9. **Quality metrics** — bcftools stats, Ti/Tv ratio check (2.0-2.1 for WGS, 2.8-3.3 for WES)
10. **Sample QC** — Sex check, relatedness (KING), concordance with metadata

### Alternative: DeepVariant Pipeline
Replace steps 5-7 with:
5. **Variant calling** — DeepVariant (ML-based, no BQSR needed)
6. **Merge** — GLnexus for joint calling
7. **Filtering** — DeepVariant quality scores (QUAL > 20)

### Common LLM Pitfalls
- Skipping BQSR when using GATK HaplotypeCaller (E009)
- Using VQSR with too few samples (<30)
- Not checking Ti/Tv ratio as a sanity check
- Genome build mismatch between reads and reference (E001)

---

## Protocol: Somatic Variant Calling (Tumor-Normal)

### When to Use
Identifying somatic mutations in cancer samples with matched normal.

### Steps
1. **Alignment and processing** — Same as germline steps 1-4 for both tumor and normal
2. **Somatic calling** — Mutect2 with matched normal, or Strelka2
3. **Panel of normals** — Create or use existing PoN for artifact filtering
4. **Filtering** — FilterMutectCalls with contamination estimation
5. **Annotation** — VEP with cancer-specific databases (COSMIC, ClinVar, OncoKB)
6. **Tumor mutational burden** — Calculate TMB (mutations/Mb)
7. **Mutational signatures** — SigProfiler or deconstructSigs for COSMIC signatures
8. **Driver gene analysis** — MutSigCV, dNdScv for driver identification
9. **Copy number** — FACETS, CNVkit, or GATK CNV for copy number alterations
10. **Structural variants** — Manta, DELLY, or GRIDSS for SVs

### Common LLM Pitfalls
- Using germline caller for somatic variants (E009)
- Not accounting for tumor purity and ploidy
- Confusing germline polymorphisms with somatic mutations
- Not using a panel of normals for artifact filtering

---

## Protocol: Structural Variant Detection

### When to Use
Identifying large genomic rearrangements (>50bp): deletions, duplications, inversions, translocations.

### Steps
1. **Short-read SV calling** — Manta (Illumina), DELLY, GRIDSS
2. **Long-read SV calling** — Sniffles2 (ONT/PacBio), cuteSV, SVIM
3. **Merging** — SURVIVOR for merging SV calls across callers
4. **Genotyping** — SVTyper, Paragraph for population-level genotyping
5. **Annotation** — AnnotSV for gene/regulatory overlap
6. **Filtering** — By quality, read support, and size
7. **Visualization** — IGV, Ribbon, or samplot for manual inspection

### Common LLM Pitfalls
- Relying on a single SV caller (low sensitivity)
- Not validating SVs with visualization or orthogonal data
- Mixing SV coordinates from different genome builds (E001)
- Incorrect breakpoint resolution in short-read data

---

## Protocol: Population Genetics / GWAS

### When to Use
Genome-wide association studies and population-level variant analysis.

### Steps
1. **Variant QC** — Genotyping rate (>95%), MAF (>0.01), HWE (p > 1e-6)
2. **Sample QC** — Missingness (<5%), sex check, relatedness (remove duplicates/relatives)
3. **Population stratification** — PCA with reference panels (1000 Genomes)
4. **Association testing** — PLINK2 or REGENIE/SAIGE for logistic/linear regression
5. **Significance threshold** — p < 5e-8 genome-wide (Bonferroni for ~1M independent tests)
6. **Manhattan plot** — Visualize genome-wide results
7. **QQ plot** — Check for inflation (genomic inflation factor lambda ~1.0)
8. **Conditional analysis** — Identify independent signals at associated loci
9. **Fine-mapping** — SUSIE, FINEMAP for causal variant identification
10. **Functional annotation** — FUMA, Open Targets for variant-to-gene mapping
11. **Replication** — Test top hits in independent cohort

### Common LLM Pitfalls
- Not correcting for population stratification
- Using wrong significance threshold (0.05 instead of 5e-8)
- Ignoring genomic inflation in QQ plot
- Confusing LD-independent SNPs with independent loci
