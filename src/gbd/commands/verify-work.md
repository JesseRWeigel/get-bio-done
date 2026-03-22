---
name: verify-work
description: Run the 12-check bioinformatics verification framework
---

<process>

## Verify Work

### Overview
Run post-hoc verification on completed phase work using the 12-check framework.

### Step 1: Collect Artifacts
Gather all output from the current phase:
- Pipeline scripts and workflow definitions
- QC reports (FASTQC, MultiQC, flagstat)
- Result files (count matrices, VCFs, DEG tables)
- Figures and visualizations
- SUMMARY files from executors

### Step 2: Build Evidence Registry
Extract verification evidence from artifacts:
- QC metrics (mapping rate, duplicate rate, quality scores)
- Statistical test results and p-value distributions
- Tool versions and container tags
- Sample identity check results
- Batch effect assessment results

### Step 3: Run Verification
Spawn gbd-verifier with:
- All phase artifacts
- Evidence registry
- Convention locks
- LLM error catalog

### Step 4: Process Verdict
Parse the VERIFICATION-REPORT.md:
- If PASS: record in state, proceed
- If PARTIAL: create targeted gap-closure for MAJOR failures
- If FAIL: create gap-closure for CRITICAL failures, block downstream

### Step 5: Route Failures
For each failure, route to the appropriate agent:
- Data quality failures → gbd-executor (re-process with adjusted parameters)
- Statistical issues → gbd-statistician (re-analyze)
- Reproducibility failures → gbd-executor (containerize, pin versions)
- Biological implausibility → gbd-researcher + gbd-executor (investigate)

### Step 6: Update State
Record verification results in STATE.md:
- Verdict hash (content-addressed)
- Pass/fail counts
- Any unresolved issues

</process>
