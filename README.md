# ai-bias-codex

This repository contains a data-first AI bias codex focused on human judgment distortions in human-AI interaction, plus the Wikipedia-backed research taxonomy used to refine the next codex pass.

Files:
- [data/ai_bias_codex.json](/Users/michaelfive/Code/mystuff/ai-bias-codex/data/ai_bias_codex.json): Current infographic dataset and SVG source of truth.
- [data/wikipedia_seed_pages.json](/Users/michaelfive/Code/mystuff/ai-bias-codex/data/wikipedia_seed_pages.json): Category-specific Wikipedia seed pages for the refined four-failure-point taxonomy.
- [data/wikipedia_candidates.json](/Users/michaelfive/Code/mystuff/ai-bias-codex/data/wikipedia_candidates.json): Deduplicated raw candidate pages produced from the current seed set.
- [data/wikipedia_taxonomy_review.json](/Users/michaelfive/Code/mystuff/ai-bias-codex/data/wikipedia_taxonomy_review.json): Curated research-stage taxonomy with accepted leaves, support pages, cross-links, confidence, and rejected pages.
- [scripts/rebuild_ai_bias_codex_from_review.py](/Users/michaelfive/Code/mystuff/ai-bias-codex/scripts/rebuild_ai_bias_codex_from_review.py): Rebuilds the infographic dataset from the reviewed Wikipedia taxonomy.
- [scripts/build_from_template.py](/Users/michaelfive/Code/mystuff/ai-bias-codex/scripts/build_from_template.py): Preferred renderer that fills the original SVG template while preserving its geometry.
- [scripts/scrape_wikipedia_candidates.py](/Users/michaelfive/Code/mystuff/ai-bias-codex/scripts/scrape_wikipedia_candidates.py): Category-aware Wikipedia link scraper that expands each seed set into deduplicated candidate pages.
- [scripts/generate_ai_bias_codex.py](/Users/michaelfive/Code/mystuff/ai-bias-codex/scripts/generate_ai_bias_codex.py): Validator and SVG generator.
- [ai_bias_codex.svg](/Users/michaelfive/Code/mystuff/ai-bias-codex/ai_bias_codex.svg): Generated infographic.

Rebuild the infographic dataset from the reviewed taxonomy:

```bash
python3 scripts/rebuild_ai_bias_codex_from_review.py data/wikipedia_taxonomy_review.json data/ai_bias_codex.json
```

Generate the infographic:

```bash
python3 scripts/build_from_template.py data/ai_bias_codex.json Cognitive_bias_codex_en.svg ai_bias_codex.svg
```

Validate the taxonomy only:

```bash
python3 scripts/generate_ai_bias_codex.py data/ai_bias_codex.json --validate-only
```

Scrape direct Wikipedia links from the configured seed pages:

```bash
python3 scripts/scrape_wikipedia_candidates.py data/wikipedia_seed_pages.json data/wikipedia_candidates.json
```

Notes:
- The refined research taxonomy is organized around four failure points:
  `Trust and Reliance Miscalibration`, `Belief Reinforcement and Selective Uptake`, `Judgment Steering by Anchors and Frames`, and `Mind-Perception and Capability Illusions`.
- Each seed category also stores a simpler public-facing display label for infographic copy.
- `data/wikipedia_taxonomy_review.json` contains the curated table, recommended codex structure, candidate inventory, and rejected-page log for the new taxonomy.
- The current infographic dataset contains `48` exact Wikipedia-linked concepts across `20` statements.
- The dataset stores `quadrant`, `statement`, `bias_name`, `one_sentence_definition`, `interaction_rationale`, `wikipedia_url`, `link_kind`, `seed_page`, and `review_status` for every leaf.
- The scraper hits the live Wikipedia API, so it needs outbound network access when you run it.
- The template renderer preserves the original codex geometry and hides unused template slots.
- One original statement wedge only provides 3 leaf slots, so the strict template build currently renders 47 visible concepts from the 48-concept dataset.
