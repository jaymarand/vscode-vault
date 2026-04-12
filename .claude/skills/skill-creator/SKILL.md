---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level, the process of creating a skill goes like this:

- Decide what you want the skill to do and roughly how it should do it
- Write a draft of the skill
- Create a few test prompts and run claude-with-access-to-the-skill on them
- Help the user evaluate the results both qualitatively and quantitatively
  - While the runs happen in the background, draft some quantitative evals if there aren't any
  - Use the `eval-viewer/generate_review.py` script to show the user the results
- Rewrite the skill based on feedback from the user's evaluation
- Repeat until you're satisfied
- Expand the test set and try again at larger scale

Your job is to figure out where the user is in this process and help them progress through these stages.

## Communicating with the user

Pay attention to context cues to understand how to phrase your communication. Briefly explain terms if you're in doubt.

---

## Creating a skill

### Capture Intent

1. What should this skill enable Claude to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?
4. Should we set up test cases to verify the skill works?

### Interview and Research

Proactively ask questions about edge cases, input/output formats, example files, success criteria, and dependencies. Check available MCPs for research if useful.

### Write the SKILL.md

- **name**: Skill identifier
- **description**: When to trigger, what it does. Make descriptions a little "pushy" to combat undertriggering.
- **the rest of the skill**

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

**Key patterns:**
- Keep SKILL.md under 500 lines
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

#### Writing Patterns

Prefer using the imperative form in instructions. Explain the **why** behind everything. If you find yourself writing ALWAYS or NEVER in all caps, reframe and explain the reasoning instead.

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts. Save to `evals/evals.json`.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema.

## Running and evaluating test cases

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Organize by iteration (`iteration-1/`, `iteration-2/`, etc.).

### Step 1: Spawn all runs in the same turn
For each test case, spawn two subagents — one with the skill, one without (baseline).

### Step 2: While runs are in progress, draft assertions
Don't wait — draft quantitative assertions for each test case.

### Step 3: Capture timing data
When each subagent completes, save `total_tokens` and `duration_ms` to `timing.json`.

### Step 4: Grade, aggregate, and launch the viewer

1. **Grade each run** — read `agents/grader.md` and evaluate assertions
2. **Aggregate** — run: `python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>`
3. **Analyst pass** — read `agents/analyzer.md` for what to look for
4. **Launch viewer**: `python eval-viewer/generate_review.py <workspace>/iteration-N --skill-name "my-skill" --benchmark <workspace>/iteration-N/benchmark.json`

### Step 5: Read the feedback
Read `feedback.json` after the user reviews. Empty feedback = looks good. Focus on test cases with specific complaints.

## Improving the skill

1. **Generalize from feedback** — don't overfit to specific examples
2. **Keep the prompt lean** — remove things that aren't pulling their weight
3. **Explain the why** — theory of mind > rigid MUSTs
4. **Look for repeated work** — if subagents all wrote similar scripts, bundle them

### The iteration loop

1. Apply improvements
2. Rerun all test cases into new `iteration-<N+1>/`
3. Launch the reviewer with `--previous-workspace`
4. Wait for user review
5. Repeat

## Description Optimization

After creating or improving a skill, offer to optimize the description.

1. Generate 20 eval queries (mix of should-trigger and should-not-trigger)
2. Review with user via `assets/eval_review.html`
3. Run optimization: `python -m scripts.run_loop --eval-set <path> --skill-path <path> --model <model-id> --max-iterations 5 --verbose`
4. Apply `best_description` from results

## Reference files

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison
- `agents/analyzer.md` — How to analyze why one version beat another
- `references/schemas.md` — JSON structures for evals, grading, etc.

---

Core loop: Draft → Test → Review → Improve → Repeat → Package.
