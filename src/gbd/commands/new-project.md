---
name: new-project
description: Initialize a new bioinformatics research project
---

<process>

## Initialize New Bioinformatics Research Project

### Step 1: Create project structure
Create the `.gbd/` directory and all required subdirectories:
- `.gbd/` — project state and config
- `.gbd/observability/sessions/` — session logs
- `.gbd/traces/` — execution traces
- `knowledge/` — research knowledge base
- `data/` — raw and processed data (gitignored for large files)
- `pipelines/` — pipeline scripts and workflows
- `results/` — analysis results
- `.scratch/` — temporary working files (gitignored)

### Step 2: Gather project information
Ask the user:
1. **Project name**: What is this research project about?
2. **Biological question**: What specific biological question are you investigating?
3. **Data types**: What sequencing/omics data will you use? (RNA-seq, WGS, WES, ChIP-seq, ATAC-seq, scRNA-seq, etc.)
4. **Organism**: What organism? (human, mouse, Drosophila, C. elegans, Arabidopsis, etc.)
5. **Model profile**: deep-analysis (default), pipeline-heavy, exploratory, review, or paper-writing?
6. **Research mode**: explore, balanced (default), exploit, or adaptive?

### Step 3: Create initial ROADMAP.md
Based on the research question, create a phase breakdown:

```markdown
# [Project Name] — Roadmap

## Phase 1: Data Acquisition and QC
**Goal**: Obtain raw sequencing data and perform comprehensive quality control

## Phase 2: Alignment and Processing
**Goal**: Align reads to reference genome and process alignments

## Phase 3: Quantification and Feature Extraction
**Goal**: Generate counts/variants/peaks from processed alignments

## Phase 4: Statistical Analysis
**Goal**: Perform differential analysis and hypothesis testing

## Phase 5: Biological Interpretation
**Goal**: Pathway analysis, functional annotation, validation

## Phase 6: Paper Writing
**Goal**: Write publication-ready manuscript
```

Adjust phases based on the specific data type and question. RNA-seq, WGS, ChIP-seq each have different phase structures.

### Step 4: Initialize state
Create STATE.md and state.json with:
- Project name and creation date
- Phase listing from ROADMAP
- Phase 1 set as active
- Research mode and autonomy mode

### Step 5: Initialize config
Create `.gbd/config.json` with user's choices.

### Step 6: Initialize git
If not already a git repo, initialize one. Add `.scratch/`, `data/raw/`, and large file patterns to `.gitignore`.
Commit the initial project structure.

### Step 7: Convention prompting
Ask if the user wants to pre-set any conventions:
- Reference genome (GRCh38, T2T-CHM13, etc.)
- Gene annotation (GENCODE, Ensembl, RefSeq)
- Aligner (STAR, BWA-MEM2, minimap2)
- Significance thresholds (FDR < 0.05, etc.)

Lock any conventions the user specifies.

### Step 8: Summary
Display:
- Project structure created
- Phases from roadmap
- Active conventions
- Next step: run `plan-phase` to begin Phase 1

</process>
