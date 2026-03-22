---
name: plan-phase
description: Plan the current phase — research, plan, and validate before execution
---

<process>

## Plan Phase

### Overview
Before execution, create validated plans for the current phase:
1. Research the domain (gbd-researcher)
2. Create plans (gbd-planner)
3. Validate plans (gbd-statistician for statistical phases)
4. Iterate until plans pass validation

### Step 1: Domain Research
Spawn gbd-researcher with:
- Phase goal from ROADMAP.md
- Current convention locks
- Research mode parameters

Collect RESEARCH.md output.

### Step 2: Plan Creation
Spawn gbd-planner with:
- Phase goal
- RESEARCH.md findings
- Convention locks
- Task sizing constraints (max 8-10 tasks per plan)

Collect PLAN-XX-YY.md files.

### Step 3: Plan Validation
For each plan, validate:
- Coverage: does the plan address all aspects of the phase goal?
- Dependencies: are task dependencies correct and acyclic?
- Feasibility: can each task be completed in one executor invocation?
- Conventions: are all required conventions locked?
- Statistical rigor: for analysis phases, spawn gbd-statistician to validate approach

### Step 4: Revision Loop
If validation returns REVISE:
1. Feed revision recommendations back to gbd-planner
2. Planner revises the plan
3. Re-validate
4. Maximum 3 iterations

If validation returns REJECT after 3 iterations:
- Present issues to user
- Ask for guidance on approach

### Step 5: Commit and Present
Once plans are validated:
1. Commit all PLAN.md files
2. Display plan summary to user
3. Show wave structure (what runs in parallel)
4. If autonomy is 'supervised': wait for user approval
5. If autonomy is 'balanced' or 'yolo': proceed to execute-phase

</process>
