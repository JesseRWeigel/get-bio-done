"""Single source of truth for all directory/file names and environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


# -- Environment Variables --------------------------------------------------

ENV_GBD_HOME = "GBD_HOME"
ENV_GBD_PROJECT = "GBD_PROJECT"
ENV_GBD_INSTALL_DIR = "GBD_INSTALL_DIR"
ENV_GBD_DEBUG = "GBD_DEBUG"
ENV_GBD_AUTONOMY = "GBD_AUTONOMY"

# -- File Names -------------------------------------------------------------

STATE_MD = "STATE.md"
STATE_JSON = "state.json"
STATE_WRITE_INTENT = ".state-write-intent"
ROADMAP_MD = "ROADMAP.md"
CONFIG_JSON = "config.json"
CONVENTIONS_JSON = "conventions.json"

PLAN_PREFIX = "PLAN"
SUMMARY_PREFIX = "SUMMARY"
RESEARCH_MD = "RESEARCH.md"
RESEARCH_DIGEST_MD = "RESEARCH-DIGEST.md"
CONTINUE_HERE_MD = ".continue-here.md"

# -- Directory Names --------------------------------------------------------

GBD_DIR = ".gbd"
OBSERVABILITY_DIR = "observability"
SESSIONS_DIR = "sessions"
TRACES_DIR = "traces"
KNOWLEDGE_DIR = "knowledge"
PAPER_DIR = "paper"
SCRATCH_DIR = ".scratch"
DATA_DIR = "data"
PIPELINES_DIR = "pipelines"
RESULTS_DIR = "results"

# -- Git --------------------------------------------------------------------

CHECKPOINT_TAG_PREFIX = "gbd-checkpoint"
COMMIT_PREFIX = "[gbd]"

# -- Autonomy Modes ---------------------------------------------------------

AUTONOMY_SUPERVISED = "supervised"
AUTONOMY_BALANCED = "balanced"
AUTONOMY_YOLO = "yolo"
VALID_AUTONOMY_MODES = {AUTONOMY_SUPERVISED, AUTONOMY_BALANCED, AUTONOMY_YOLO}

# -- Research Modes ---------------------------------------------------------

RESEARCH_EXPLORE = "explore"
RESEARCH_BALANCED = "balanced"
RESEARCH_EXPLOIT = "exploit"
RESEARCH_ADAPTIVE = "adaptive"
VALID_RESEARCH_MODES = {RESEARCH_EXPLORE, RESEARCH_BALANCED, RESEARCH_EXPLOIT, RESEARCH_ADAPTIVE}

# -- Model Tiers ------------------------------------------------------------

TIER_1 = "tier-1"  # Highest capability
TIER_2 = "tier-2"  # Balanced
TIER_3 = "tier-3"  # Fastest

# -- Verification Severity --------------------------------------------------

SEVERITY_CRITICAL = "CRITICAL"  # Blocks all downstream work
SEVERITY_MAJOR = "MAJOR"        # Must resolve before conclusions
SEVERITY_MINOR = "MINOR"        # Must resolve before publication
SEVERITY_NOTE = "NOTE"          # Informational

# -- Convention Lock Fields (Bioinformatics) --------------------------------

CONVENTION_FIELDS = [
    "reference_genome",             # GRCh38, GRCm39, T2T-CHM13, etc.
    "gene_annotation_source",       # GENCODE v44, Ensembl 110, RefSeq, etc.
    "aligner",                      # STAR, HISAT2, BWA-MEM2, minimap2, etc.
    "variant_caller",               # GATK HaplotypeCaller, DeepVariant, Strelka2, etc.
    "significance_threshold",       # FDR < 0.05, p < 5e-8 (GWAS), etc.
    "multiple_testing_correction",  # Benjamini-Hochberg, Bonferroni, q-value, etc.
    "normalization_method",         # DESeq2 median-of-ratios, TMM, TPM, RPKM, etc.
    "quality_thresholds",           # MAPQ >= 30, base quality >= 20, etc.
    "filtering_criteria",           # min read count, MAF > 0.01, etc.
    "container_env_versions",       # Docker/Singularity image tags, conda env YAML, etc.
]

# -- Verification Checks ---------------------------------------------------

VERIFICATION_CHECKS = [
    "data_quality",                 # FASTQC, MultiQC, contamination screening
    "alignment_quality",            # Mapping rate, duplicate rate, insert size distribution
    "known_sample_validation",      # Positive/negative controls, spike-ins, known variants
    "pipeline_reproducibility",     # Same inputs produce same outputs (containerized, version-pinned)
    "statistical_validity",         # Appropriate tests, assumptions met, effect sizes reported
    "fdr_control",                  # Multiple testing correction applied and validated
    "batch_effect_assessment",      # PCA/MDS visualization, ComBat or similar if needed
    "biological_plausibility",      # Results consistent with known biology, pathway analysis
    "sample_identity",              # Sex check, relatedness, concordance with metadata
    "version_pinning",              # All tools, references, and containers version-locked
    "literature_comparison",        # Results compared with published studies in the field
    "visualization_accuracy",       # Plots correctly represent underlying data, axes labeled
]


@dataclass(frozen=True)
class ProjectLayout:
    """Resolved paths for a GBD project."""

    root: Path

    @property
    def gbd_dir(self) -> Path:
        return self.root / GBD_DIR

    @property
    def state_md(self) -> Path:
        return self.gbd_dir / STATE_MD

    @property
    def state_json(self) -> Path:
        return self.gbd_dir / STATE_JSON

    @property
    def state_write_intent(self) -> Path:
        return self.gbd_dir / STATE_WRITE_INTENT

    @property
    def roadmap_md(self) -> Path:
        return self.gbd_dir / ROADMAP_MD

    @property
    def config_json(self) -> Path:
        return self.gbd_dir / CONFIG_JSON

    @property
    def conventions_json(self) -> Path:
        return self.gbd_dir / CONVENTIONS_JSON

    @property
    def observability_dir(self) -> Path:
        return self.gbd_dir / OBSERVABILITY_DIR

    @property
    def sessions_dir(self) -> Path:
        return self.observability_dir / SESSIONS_DIR

    @property
    def traces_dir(self) -> Path:
        return self.gbd_dir / TRACES_DIR

    @property
    def knowledge_dir(self) -> Path:
        return self.root / KNOWLEDGE_DIR

    @property
    def paper_dir(self) -> Path:
        return self.root / PAPER_DIR

    @property
    def scratch_dir(self) -> Path:
        return self.root / SCRATCH_DIR

    @property
    def data_dir(self) -> Path:
        return self.root / DATA_DIR

    @property
    def pipelines_dir(self) -> Path:
        return self.root / PIPELINES_DIR

    @property
    def results_dir(self) -> Path:
        return self.root / RESULTS_DIR

    @property
    def continue_here(self) -> Path:
        return self.gbd_dir / CONTINUE_HERE_MD

    def phase_dir(self, phase: str) -> Path:
        return self.root / f"phase-{phase}"

    def plan_path(self, phase: str, plan_number: str) -> Path:
        return self.phase_dir(phase) / f"{PLAN_PREFIX}-{plan_number}.md"

    def summary_path(self, phase: str, plan_number: str) -> Path:
        return self.phase_dir(phase) / f"{SUMMARY_PREFIX}-{plan_number}.md"

    def ensure_dirs(self) -> None:
        """Create all required directories."""
        for d in [
            self.gbd_dir,
            self.observability_dir,
            self.sessions_dir,
            self.traces_dir,
            self.knowledge_dir,
            self.scratch_dir,
            self.data_dir,
            self.pipelines_dir,
            self.results_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)


def find_project_root(start: Path | None = None) -> Path:
    """Walk up from start (or cwd) looking for .gbd/ directory."""
    current = start or Path.cwd()
    while current != current.parent:
        if (current / GBD_DIR).is_dir():
            return current
        current = current.parent
    raise FileNotFoundError(
        f"No {GBD_DIR}/ directory found. Run 'gbd init' to create a project."
    )


def get_layout(start: Path | None = None) -> ProjectLayout:
    """Get the project layout, finding the root automatically."""
    env_project = os.environ.get(ENV_GBD_PROJECT)
    if env_project:
        return ProjectLayout(root=Path(env_project))
    return ProjectLayout(root=find_project_root(start))
