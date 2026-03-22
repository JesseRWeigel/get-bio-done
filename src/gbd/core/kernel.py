"""Content-addressed verification kernel.

Runs predicates over evidence registries and produces SHA-256 verdicts.
Adapted from GPD's kernel.py for bioinformatics pipeline verification.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from .constants import VERIFICATION_CHECKS, SEVERITY_CRITICAL, SEVERITY_MAJOR, SEVERITY_MINOR, SEVERITY_NOTE


class Severity(str, Enum):
    CRITICAL = SEVERITY_CRITICAL
    MAJOR = SEVERITY_MAJOR
    MINOR = SEVERITY_MINOR
    NOTE = SEVERITY_NOTE


@dataclass
class CheckResult:
    """Result of a single verification check."""

    check_id: str
    name: str
    status: str  # PASS | FAIL | SKIP | WARN
    severity: Severity
    message: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class Verdict:
    """Complete verification verdict with content-addressed hashes."""

    registry_hash: str
    predicates_hash: str
    verdict_hash: str
    overall: str  # PASS | FAIL | PARTIAL
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    results: dict[str, CheckResult] = field(default_factory=dict)
    summary: str = ""

    @property
    def critical_failures(self) -> list[CheckResult]:
        return [
            r
            for r in self.results.values()
            if r.status == "FAIL" and r.severity == Severity.CRITICAL
        ]

    @property
    def major_failures(self) -> list[CheckResult]:
        return [
            r
            for r in self.results.values()
            if r.status == "FAIL" and r.severity == Severity.MAJOR
        ]

    @property
    def all_failures(self) -> list[CheckResult]:
        return [r for r in self.results.values() if r.status == "FAIL"]

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == "PASS")

    @property
    def fail_count(self) -> int:
        return sum(1 for r in self.results.values() if r.status == "FAIL")

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_hash": self.registry_hash,
            "predicates_hash": self.predicates_hash,
            "verdict_hash": self.verdict_hash,
            "overall": self.overall,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "results": {
                k: {
                    "check_id": v.check_id,
                    "name": v.name,
                    "status": v.status,
                    "severity": v.severity.value,
                    "message": v.message,
                    "evidence": v.evidence,
                    "suggestions": v.suggestions,
                }
                for k, v in self.results.items()
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# -- Predicate Type ---------------------------------------------------------

# A predicate takes an evidence registry and returns a CheckResult
Predicate = Callable[[dict[str, Any]], CheckResult]


# -- Built-in Bioinformatics Predicates ------------------------------------

def check_data_quality(evidence: dict[str, Any]) -> CheckResult:
    """Check raw data quality (FASTQC, contamination, adapter content)."""
    qc_reports = evidence.get("qc_reports", [])
    qc_failures = evidence.get("qc_failures", [])

    if not qc_reports:
        return CheckResult(
            check_id="data_quality",
            name="Data Quality",
            status="SKIP",
            severity=Severity.CRITICAL,
            message="No QC reports provided.",
        )

    if qc_failures:
        return CheckResult(
            check_id="data_quality",
            name="Data Quality",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"Found {len(qc_failures)} QC failure(s).",
            evidence={"failures": qc_failures},
            suggestions=[
                f"Address QC issue: {f}" for f in qc_failures[:5]
            ],
        )

    return CheckResult(
        check_id="data_quality",
        name="Data Quality",
        status="PASS",
        severity=Severity.CRITICAL,
        message=f"All {len(qc_reports)} QC reports passed.",
    )


def check_alignment_quality(evidence: dict[str, Any]) -> CheckResult:
    """Check alignment metrics (mapping rate, duplicates, insert size)."""
    mapping_rate = evidence.get("mapping_rate")
    duplicate_rate = evidence.get("duplicate_rate")
    min_mapping_rate = evidence.get("min_mapping_rate", 0.80)

    if mapping_rate is None:
        return CheckResult(
            check_id="alignment_quality",
            name="Alignment Quality",
            status="SKIP",
            severity=Severity.CRITICAL,
            message="No alignment metrics provided.",
        )

    issues = []
    if mapping_rate < min_mapping_rate:
        issues.append(f"Mapping rate {mapping_rate:.1%} below threshold {min_mapping_rate:.1%}")
    if duplicate_rate is not None and duplicate_rate > 0.50:
        issues.append(f"Duplicate rate {duplicate_rate:.1%} exceeds 50%")

    if issues:
        return CheckResult(
            check_id="alignment_quality",
            name="Alignment Quality",
            status="FAIL",
            severity=Severity.CRITICAL,
            message="; ".join(issues),
            evidence={"mapping_rate": mapping_rate, "duplicate_rate": duplicate_rate},
            suggestions=["Check library preparation", "Verify reference genome match"],
        )

    return CheckResult(
        check_id="alignment_quality",
        name="Alignment Quality",
        status="PASS",
        severity=Severity.CRITICAL,
        message=f"Mapping rate {mapping_rate:.1%}, duplicate rate {duplicate_rate:.1%}.",
    )


def check_known_sample_validation(evidence: dict[str, Any]) -> CheckResult:
    """Check positive/negative controls and spike-ins."""
    controls_present = evidence.get("controls_present", False)
    controls_passed = evidence.get("controls_passed", [])
    controls_failed = evidence.get("controls_failed", [])

    if not controls_present:
        return CheckResult(
            check_id="known_sample_validation",
            name="Known Sample Validation",
            status="WARN",
            severity=Severity.MAJOR,
            message="No positive/negative controls included.",
            suggestions=["Include spike-in controls (e.g., ERCC) in future experiments."],
        )

    if controls_failed:
        return CheckResult(
            check_id="known_sample_validation",
            name="Known Sample Validation",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"{len(controls_failed)} control(s) failed validation.",
            evidence={"failed": controls_failed},
        )

    return CheckResult(
        check_id="known_sample_validation",
        name="Known Sample Validation",
        status="PASS",
        severity=Severity.MAJOR,
        message=f"All {len(controls_passed)} control(s) passed.",
    )


def check_pipeline_reproducibility(evidence: dict[str, Any]) -> CheckResult:
    """Check pipeline is containerized and version-pinned."""
    containerized = evidence.get("containerized", False)
    versions_pinned = evidence.get("versions_pinned", False)
    workflow_manager = evidence.get("workflow_manager")  # Nextflow, Snakemake, WDL

    issues = []
    if not containerized:
        issues.append("Pipeline not containerized (Docker/Singularity)")
    if not versions_pinned:
        issues.append("Tool versions not pinned")

    if issues:
        return CheckResult(
            check_id="pipeline_reproducibility",
            name="Pipeline Reproducibility",
            status="FAIL",
            severity=Severity.CRITICAL,
            message="; ".join(issues),
            suggestions=[
                "Use Docker/Singularity containers with fixed tags",
                "Pin all tool versions in environment YAML or Dockerfile",
                "Use a workflow manager (Nextflow, Snakemake, WDL)",
            ],
        )

    return CheckResult(
        check_id="pipeline_reproducibility",
        name="Pipeline Reproducibility",
        status="PASS",
        severity=Severity.CRITICAL,
        message=f"Pipeline containerized, versions pinned. Workflow: {workflow_manager or 'N/A'}.",
    )


def check_statistical_validity(evidence: dict[str, Any]) -> CheckResult:
    """Check statistical tests are appropriate and assumptions met."""
    tests_used = evidence.get("statistical_tests", [])
    assumptions_verified = evidence.get("assumptions_verified", [])
    assumptions_violated = evidence.get("assumptions_violated", [])

    if not tests_used:
        return CheckResult(
            check_id="statistical_validity",
            name="Statistical Validity",
            status="SKIP",
            severity=Severity.MAJOR,
            message="No statistical tests reported.",
        )

    if assumptions_violated:
        return CheckResult(
            check_id="statistical_validity",
            name="Statistical Validity",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{len(assumptions_violated)} test assumption(s) violated.",
            evidence={"violated": assumptions_violated},
            suggestions=["Use non-parametric alternatives or transform data."],
        )

    return CheckResult(
        check_id="statistical_validity",
        name="Statistical Validity",
        status="PASS",
        severity=Severity.MAJOR,
        message=f"{len(tests_used)} statistical test(s) validated.",
    )


def check_fdr_control(evidence: dict[str, Any]) -> CheckResult:
    """Check that multiple testing correction is properly applied."""
    correction_method = evidence.get("correction_method")
    total_tests = evidence.get("total_tests", 0)
    fdr_threshold = evidence.get("fdr_threshold")

    if total_tests <= 1:
        return CheckResult(
            check_id="fdr_control",
            name="FDR Control",
            status="SKIP",
            severity=Severity.MAJOR,
            message="Single test — no multiple testing correction needed.",
        )

    if not correction_method:
        return CheckResult(
            check_id="fdr_control",
            name="FDR Control",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"{total_tests} tests performed without multiple testing correction.",
            suggestions=[
                "Apply Benjamini-Hochberg FDR correction",
                "Report adjusted p-values alongside raw p-values",
            ],
        )

    return CheckResult(
        check_id="fdr_control",
        name="FDR Control",
        status="PASS",
        severity=Severity.CRITICAL,
        message=f"FDR controlled via {correction_method} (threshold: {fdr_threshold}).",
    )


def check_batch_effect(evidence: dict[str, Any]) -> CheckResult:
    """Check batch effects are assessed and mitigated."""
    batch_assessment_done = evidence.get("batch_assessment_done", False)
    batch_effects_detected = evidence.get("batch_effects_detected", False)
    batch_correction_applied = evidence.get("batch_correction_applied", False)

    if not batch_assessment_done:
        return CheckResult(
            check_id="batch_effect_assessment",
            name="Batch Effect Assessment",
            status="WARN",
            severity=Severity.MAJOR,
            message="No batch effect assessment performed.",
            suggestions=[
                "Run PCA/MDS colored by batch to visualize batch effects",
                "Use ComBat, limma removeBatchEffect, or include batch as covariate",
            ],
        )

    if batch_effects_detected and not batch_correction_applied:
        return CheckResult(
            check_id="batch_effect_assessment",
            name="Batch Effect Assessment",
            status="FAIL",
            severity=Severity.MAJOR,
            message="Batch effects detected but not corrected.",
            evidence={"detected": True, "corrected": False},
        )

    return CheckResult(
        check_id="batch_effect_assessment",
        name="Batch Effect Assessment",
        status="PASS",
        severity=Severity.MAJOR,
        message="Batch effects assessed" + (" and corrected." if batch_correction_applied else ", none detected."),
    )


def check_biological_plausibility(evidence: dict[str, Any]) -> CheckResult:
    """Check results are biologically plausible."""
    pathway_analysis = evidence.get("pathway_analysis_done", False)
    known_biology_consistent = evidence.get("known_biology_consistent")
    implausible_results = evidence.get("implausible_results", [])

    if implausible_results:
        return CheckResult(
            check_id="biological_plausibility",
            name="Biological Plausibility",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{len(implausible_results)} biologically implausible result(s).",
            evidence={"implausible": implausible_results},
            suggestions=["Verify sample labeling", "Check for technical artifacts"],
        )

    if not pathway_analysis:
        return CheckResult(
            check_id="biological_plausibility",
            name="Biological Plausibility",
            status="WARN",
            severity=Severity.MAJOR,
            message="No pathway/GO enrichment analysis performed.",
            suggestions=["Run gene set enrichment analysis (GSEA, g:Profiler, clusterProfiler)"],
        )

    return CheckResult(
        check_id="biological_plausibility",
        name="Biological Plausibility",
        status="PASS",
        severity=Severity.MAJOR,
        message="Results consistent with known biology.",
    )


def check_sample_identity(evidence: dict[str, Any]) -> CheckResult:
    """Check sample identity (sex check, relatedness, metadata concordance)."""
    identity_checks = evidence.get("identity_checks", [])
    identity_mismatches = evidence.get("identity_mismatches", [])

    if not identity_checks:
        return CheckResult(
            check_id="sample_identity",
            name="Sample Identity",
            status="WARN",
            severity=Severity.CRITICAL,
            message="No sample identity checks performed.",
            suggestions=[
                "Run sex check against metadata",
                "Check sample relatedness (KING, Peddy)",
                "Verify SNP fingerprinting concordance",
            ],
        )

    if identity_mismatches:
        return CheckResult(
            check_id="sample_identity",
            name="Sample Identity",
            status="FAIL",
            severity=Severity.CRITICAL,
            message=f"{len(identity_mismatches)} sample identity mismatch(es).",
            evidence={"mismatches": identity_mismatches},
        )

    return CheckResult(
        check_id="sample_identity",
        name="Sample Identity",
        status="PASS",
        severity=Severity.CRITICAL,
        message=f"All {len(identity_checks)} identity check(s) passed.",
    )


def check_version_pinning(evidence: dict[str, Any]) -> CheckResult:
    """Check all tools, references, and containers are version-locked."""
    tools_versioned = evidence.get("tools_versioned", [])
    tools_unversioned = evidence.get("tools_unversioned", [])
    reference_version = evidence.get("reference_version")

    issues = []
    if tools_unversioned:
        issues.append(f"{len(tools_unversioned)} tool(s) without pinned versions")
    if not reference_version:
        issues.append("Reference genome version not recorded")

    if issues:
        return CheckResult(
            check_id="version_pinning",
            name="Version Pinning",
            status="FAIL",
            severity=Severity.MAJOR,
            message="; ".join(issues),
            evidence={"unversioned": tools_unversioned},
            suggestions=["Pin all tool versions", "Record reference genome build and annotation version"],
        )

    return CheckResult(
        check_id="version_pinning",
        name="Version Pinning",
        status="PASS",
        severity=Severity.MAJOR,
        message=f"All {len(tools_versioned)} tools version-pinned. Reference: {reference_version}.",
    )


def check_literature_comparison(evidence: dict[str, Any]) -> CheckResult:
    """Check results compared with published studies."""
    comparisons_made = evidence.get("literature_comparisons", [])
    discrepancies = evidence.get("literature_discrepancies", [])

    if not comparisons_made:
        return CheckResult(
            check_id="literature_comparison",
            name="Literature Comparison",
            status="WARN",
            severity=Severity.MINOR,
            message="No comparisons with published studies.",
            suggestions=["Compare key findings with relevant published datasets."],
        )

    if discrepancies:
        return CheckResult(
            check_id="literature_comparison",
            name="Literature Comparison",
            status="FAIL",
            severity=Severity.MAJOR,
            message=f"{len(discrepancies)} discrepancy/ies with published results.",
            evidence={"discrepancies": discrepancies},
        )

    return CheckResult(
        check_id="literature_comparison",
        name="Literature Comparison",
        status="PASS",
        severity=Severity.MINOR,
        message=f"Consistent with {len(comparisons_made)} published study/ies.",
    )


def check_visualization_accuracy(evidence: dict[str, Any]) -> CheckResult:
    """Check plots correctly represent underlying data."""
    plots_reviewed = evidence.get("plots_reviewed", 0)
    plot_issues = evidence.get("plot_issues", [])

    if plots_reviewed == 0:
        return CheckResult(
            check_id="visualization_accuracy",
            name="Visualization Accuracy",
            status="SKIP",
            severity=Severity.MINOR,
            message="No plots to review.",
        )

    if plot_issues:
        return CheckResult(
            check_id="visualization_accuracy",
            name="Visualization Accuracy",
            status="FAIL",
            severity=Severity.MINOR,
            message=f"{len(plot_issues)} visualization issue(s) found.",
            evidence={"issues": plot_issues},
        )

    return CheckResult(
        check_id="visualization_accuracy",
        name="Visualization Accuracy",
        status="PASS",
        severity=Severity.MINOR,
        message=f"All {plots_reviewed} plot(s) accurately represent data.",
    )


# -- Default predicate registry ---------------------------------------------

DEFAULT_PREDICATES: dict[str, Predicate] = {
    "data_quality": check_data_quality,
    "alignment_quality": check_alignment_quality,
    "known_sample_validation": check_known_sample_validation,
    "pipeline_reproducibility": check_pipeline_reproducibility,
    "statistical_validity": check_statistical_validity,
    "fdr_control": check_fdr_control,
    "batch_effect_assessment": check_batch_effect,
    "biological_plausibility": check_biological_plausibility,
    "sample_identity": check_sample_identity,
    "version_pinning": check_version_pinning,
    "literature_comparison": check_literature_comparison,
    "visualization_accuracy": check_visualization_accuracy,
}


# -- Verification Kernel ----------------------------------------------------

class VerificationKernel:
    """Content-addressed verification kernel.

    Runs predicates over evidence registries and produces
    SHA-256 verdicts for reproducibility and tamper-evidence.
    """

    def __init__(self, predicates: dict[str, Predicate] | None = None):
        self.predicates = predicates or dict(DEFAULT_PREDICATES)

    def _hash(self, data: str) -> str:
        return f"sha256:{hashlib.sha256(data.encode()).hexdigest()}"

    def verify(self, evidence: dict[str, Any]) -> Verdict:
        """Run all predicates against evidence and produce a verdict."""
        # Hash inputs
        evidence_json = json.dumps(evidence, sort_keys=True, default=str)
        registry_hash = self._hash(evidence_json)

        predicate_names = json.dumps(sorted(self.predicates.keys()))
        predicates_hash = self._hash(predicate_names)

        # Run predicates
        results: dict[str, CheckResult] = {}
        for check_id, predicate in self.predicates.items():
            try:
                result = predicate(evidence)
                results[check_id] = result
            except Exception as e:
                results[check_id] = CheckResult(
                    check_id=check_id,
                    name=check_id.replace("_", " ").title(),
                    status="FAIL",
                    severity=Severity.MAJOR,
                    message=f"Predicate raised exception: {e}",
                )

        # Determine overall status
        has_critical_fail = any(
            r.status == "FAIL" and r.severity == Severity.CRITICAL
            for r in results.values()
        )
        has_major_fail = any(
            r.status == "FAIL" and r.severity == Severity.MAJOR
            for r in results.values()
        )

        if has_critical_fail:
            overall = "FAIL"
        elif has_major_fail:
            overall = "PARTIAL"
        else:
            overall = "PASS"

        # Hash the results for tamper-evidence
        results_json = json.dumps(
            {k: v.message for k, v in results.items()},
            sort_keys=True,
        )
        verdict_hash = self._hash(
            f"{registry_hash}:{predicates_hash}:{results_json}"
        )

        # Build summary
        pass_count = sum(1 for r in results.values() if r.status == "PASS")
        fail_count = sum(1 for r in results.values() if r.status == "FAIL")
        skip_count = sum(1 for r in results.values() if r.status == "SKIP")
        warn_count = sum(1 for r in results.values() if r.status == "WARN")

        summary = (
            f"{overall}: {pass_count} passed, {fail_count} failed, "
            f"{warn_count} warnings, {skip_count} skipped "
            f"out of {len(results)} checks."
        )

        return Verdict(
            registry_hash=registry_hash,
            predicates_hash=predicates_hash,
            verdict_hash=verdict_hash,
            overall=overall,
            results=results,
            summary=summary,
        )
