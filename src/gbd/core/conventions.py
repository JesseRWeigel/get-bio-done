"""Convention lock management for bioinformatics pipeline consistency.

Ensures analysis parameters don't drift across phases of a research project.
Adapted from GPD's conventions.py for bioinformatics.
"""

from __future__ import annotations

from typing import Any

from .constants import CONVENTION_FIELDS
from .state import StateEngine, ConventionLock


# -- Convention Field Descriptions ------------------------------------------

CONVENTION_DESCRIPTIONS: dict[str, str] = {
    "reference_genome": (
        "Which reference genome assembly to use: GRCh38/hg38 (human, current standard), "
        "T2T-CHM13 (telomere-to-telomere, most complete), GRCh37/hg19 (legacy), "
        "GRCm39/mm39 (mouse), or other organism-specific builds. Include patch level."
    ),
    "gene_annotation_source": (
        "Gene annotation database and version: GENCODE (v44, v45 — comprehensive, includes "
        "lncRNAs), Ensembl (release 110, 111), RefSeq (NCBI — clinical standard), "
        "or organism-specific databases (WormBase, FlyBase, TAIR)."
    ),
    "aligner": (
        "Read alignment tool: STAR (RNA-seq splice-aware), HISAT2 (RNA-seq, memory efficient), "
        "BWA-MEM2 (DNA-seq, WGS/WES), minimap2 (long reads, ONT/PacBio), "
        "Bowtie2 (ChIP-seq, small genomes), Salmon/Kallisto (pseudo-alignment for quantification)."
    ),
    "variant_caller": (
        "Variant calling tool: GATK HaplotypeCaller (germline gold standard), "
        "DeepVariant (ML-based, high accuracy), Strelka2 (somatic), "
        "Mutect2 (somatic with matched normal), FreeBayes (population), "
        "DRAGEN (hardware accelerated), bcftools mpileup (lightweight)."
    ),
    "significance_threshold": (
        "Statistical significance cutoff: FDR < 0.05 (standard for differential expression), "
        "p < 5e-8 (GWAS genome-wide significance), FDR < 0.1 (discovery), "
        "FDR < 0.01 (stringent). Specify for each analysis type."
    ),
    "multiple_testing_correction": (
        "Multiple testing correction method: Benjamini-Hochberg (FDR, standard), "
        "Bonferroni (conservative, for few tests), Storey q-value (less conservative), "
        "Westfall-Young permutation (preserves correlation structure)."
    ),
    "normalization_method": (
        "Data normalization approach: DESeq2 median-of-ratios (RNA-seq counts), "
        "TMM/edgeR (RNA-seq counts), TPM (cross-sample comparison), "
        "RPKM/FPKM (within-sample, deprecated for cross-sample), "
        "quantile normalization (microarray), VOOM (RNA-seq for limma)."
    ),
    "quality_thresholds": (
        "Quality filtering cutoffs: MAPQ >= 30 (uniquely mapped), "
        "base quality >= 20 (99% accuracy), Phred >= 30 (99.9%), "
        "read length >= 50bp, adapter trimming settings (Trimmomatic/fastp parameters)."
    ),
    "filtering_criteria": (
        "Feature filtering rules: minimum read count per gene (e.g., CPM > 1 in N samples), "
        "MAF > 0.01 (common variants), genotyping rate > 95%, "
        "HWE p > 1e-6 (population genetics), missingness < 5%."
    ),
    "container_env_versions": (
        "Reproducibility pinning: Docker/Singularity image tags with SHA digests, "
        "conda environment YAML with exact versions, Bioconductor release version, "
        "workflow manager version (Nextflow DSL2, Snakemake 8.x, WDL 1.1)."
    ),
}

# -- Convention Validation --------------------------------------------------

# Common valid values for quick validation
CONVENTION_EXAMPLES: dict[str, list[str]] = {
    "reference_genome": [
        "GRCh38 (hg38) — Genome Reference Consortium, patch 14",
        "T2T-CHM13v2.0 — Telomere-to-telomere, most complete human reference",
        "GRCh37 (hg19) — Legacy, for compatibility with older datasets",
        "GRCm39 (mm39) — Mouse, current",
    ],
    "gene_annotation_source": [
        "GENCODE v44 (human, comprehensive)",
        "Ensembl release 111",
        "RefSeq GCF_000001405.40",
    ],
    "aligner": [
        "STAR 2.7.11b (RNA-seq, splice-aware)",
        "BWA-MEM2 2.2.1 (WGS/WES)",
        "minimap2 2.28 (long reads)",
        "Salmon 1.10.3 (pseudo-alignment)",
    ],
    "significance_threshold": [
        "FDR < 0.05 (Benjamini-Hochberg adjusted)",
        "p < 5e-8 (GWAS genome-wide significance)",
        "FDR < 0.1 (discovery analysis)",
    ],
    "normalization_method": [
        "DESeq2 median-of-ratios (RNA-seq count data)",
        "TMM (edgeR, RNA-seq)",
        "TPM (cross-sample transcript abundance)",
    ],
}


def get_field_description(field: str) -> str:
    """Get the description for a convention field."""
    return CONVENTION_DESCRIPTIONS.get(field, f"Convention field: {field}")


def get_field_examples(field: str) -> list[str]:
    """Get example values for a convention field."""
    return CONVENTION_EXAMPLES.get(field, [])


def list_all_fields() -> list[dict[str, Any]]:
    """List all convention fields with descriptions and examples."""
    return [
        {
            "field": f,
            "description": get_field_description(f),
            "examples": get_field_examples(f),
        }
        for f in CONVENTION_FIELDS
    ]


def check_conventions(engine: StateEngine) -> dict[str, Any]:
    """Check which conventions are locked and which are missing.

    Returns a report dict with locked, unlocked, and coverage stats.
    """
    state = engine.load()
    locked = {}
    unlocked = []

    for field in CONVENTION_FIELDS:
        if field in state.conventions:
            locked[field] = {
                "value": state.conventions[field].value,
                "locked_by": state.conventions[field].locked_by,
                "rationale": state.conventions[field].rationale,
            }
        else:
            unlocked.append(field)

    return {
        "locked": locked,
        "unlocked": unlocked,
        "coverage": f"{len(locked)}/{len(CONVENTION_FIELDS)}",
        "coverage_pct": round(100 * len(locked) / len(CONVENTION_FIELDS), 1)
        if CONVENTION_FIELDS
        else 100.0,
    }


def diff_conventions(
    engine: StateEngine,
    proposed: dict[str, str],
) -> dict[str, Any]:
    """Compare proposed convention values against current locks.

    Returns conflicts, new fields, and matching fields.
    """
    state = engine.load()
    conflicts = {}
    new_fields = {}
    matching = {}

    for field, proposed_value in proposed.items():
        if field in state.conventions:
            current = state.conventions[field].value
            if current != proposed_value:
                conflicts[field] = {
                    "current": current,
                    "proposed": proposed_value,
                }
            else:
                matching[field] = current
        else:
            new_fields[field] = proposed_value

    return {
        "conflicts": conflicts,
        "new_fields": new_fields,
        "matching": matching,
        "has_conflicts": bool(conflicts),
    }
