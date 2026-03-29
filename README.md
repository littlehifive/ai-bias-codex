# ai-bias-codex

This repository now contains a data-first AI bias codex focused on biases and failure patterns that show up in human-AI interaction.

Files:
- [data/ai_bias_codex.json](/Users/michaelfive/Code/mystuff/ai-bias-codex/data/ai_bias_codex.json): Curated taxonomy with 4 quadrants, 20 statements, and 80 linked leaf concepts.
- [data/wikipedia_seed_pages.json](/Users/michaelfive/Code/mystuff/ai-bias-codex/data/wikipedia_seed_pages.json): Seed pages used to drive pass-one discovery.
- [scripts/build_from_template.py](/Users/michaelfive/Code/mystuff/ai-bias-codex/scripts/build_from_template.py): Preferred renderer that fills the original SVG template while preserving its geometry.
- [scripts/scrape_wikipedia_candidates.py](/Users/michaelfive/Code/mystuff/ai-bias-codex/scripts/scrape_wikipedia_candidates.py): Wikipedia link scraper scaffold for reproducing the discovery pass.
- [scripts/generate_ai_bias_codex.py](/Users/michaelfive/Code/mystuff/ai-bias-codex/scripts/generate_ai_bias_codex.py): Validator and SVG generator.
- [ai_bias_codex.svg](/Users/michaelfive/Code/mystuff/ai-bias-codex/ai_bias_codex.svg): Generated infographic.

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
- The dataset stores `quadrant`, `statement`, `bias_name`, `one_sentence_definition`, `interaction_rationale`, `wikipedia_url`, `link_kind`, `seed_page`, and `review_status` for every leaf.
- Current link coverage is `77` exact pages and `3` section anchors.
- The scraper hits the live Wikipedia API, so it needs outbound network access when you run it.
- The template renderer preserves the original codex geometry and hides unused template slots.
- Two original statement wedges only provide 3 leaf slots, so the strict template build currently renders 78 visible concepts from the 80-concept dataset.
