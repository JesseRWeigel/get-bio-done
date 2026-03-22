"""Research contracts — Pydantic models for hypotheses, deliverables, and acceptance tests.

Adapted from GPD's contracts.py for bioinformatics research.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class Hypothesis(BaseModel):
    """A biological hypothesis to be tested or validated."""

    id: str
    statement: str
    hypothesis_type: str = "differential_expression"  # differential_expression | variant_association | pathway_enrichment | functional_annotation | structural_prediction
    assumptions: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)  # Other hypothesis IDs
    status: str = "untested"  # untested | supported | refuted | inconclusive


class Deliverable(BaseModel):
    """An expected output artifact from a phase/plan."""

    id: str
    description: str
    artifact_type: str  # alignment | variant_calls | expression_matrix | figure | table | manuscript_section | pipeline_script | qc_report
    file_path: str = ""
    acceptance_tests: list[str] = Field(default_factory=list)
    status: str = "pending"  # pending | delivered | verified | rejected


class AcceptanceTest(BaseModel):
    """A concrete test for a deliverable."""

    id: str
    description: str
    test_type: str  # existence | content | statistical_validity | reproducibility | biological_plausibility
    predicate: str = ""  # Human-readable predicate
    status: str = "pending"  # pending | passed | failed


class ForbiddenProxy(BaseModel):
    """Something that must NOT be used as evidence of completion.

    Prevents agents from claiming success based on superficial signals.
    """

    description: str
    reason: str


class ResearchContract(BaseModel):
    """A complete research contract for a phase or plan.

    Defines what must be achieved, how to verify it, and what NOT to accept.
    """

    phase_id: str
    plan_id: str = ""
    goal: str

    hypotheses: list[Hypothesis] = Field(default_factory=list)
    deliverables: list[Deliverable] = Field(default_factory=list)
    acceptance_tests: list[AcceptanceTest] = Field(default_factory=list)

    forbidden_proxies: list[ForbiddenProxy] = Field(
        default_factory=lambda: [
            ForbiddenProxy(
                description="Agent stating 'analysis is complete' without output files",
                reason="Result files must exist on disk and pass QC checks.",
            ),
            ForbiddenProxy(
                description="P-values reported without multiple testing correction",
                reason="All genome-wide tests must apply FDR or Bonferroni correction.",
            ),
            ForbiddenProxy(
                description="Pipeline output without reproducibility evidence",
                reason="All pipelines must be containerized or have pinned dependency versions.",
            ),
            ForbiddenProxy(
                description="Biological interpretation without statistical backing",
                reason="Pathway/GO enrichment claims must include corrected p-values and effect sizes.",
            ),
        ]
    )

    def all_hypotheses_resolved(self) -> bool:
        return all(h.status in ("supported", "refuted") for h in self.hypotheses)

    def all_deliverables_verified(self) -> bool:
        return all(d.status == "verified" for d in self.deliverables)

    def all_tests_passed(self) -> bool:
        return all(t.status == "passed" for t in self.acceptance_tests)


class AgentReturn(BaseModel):
    """Structured return envelope from subagents.

    Every subagent MUST produce this in their SUMMARY.md.
    The orchestrator uses this — not prose — to determine success.
    """

    status: str  # completed | checkpoint | blocked | failed
    files_written: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    hypotheses_tested: list[str] = Field(default_factory=list)  # Hypothesis IDs
    conventions_proposed: dict[str, str] = Field(default_factory=dict)
    verification_evidence: dict[str, Any] = Field(default_factory=dict)
