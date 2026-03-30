# The Human-AI Interaction Bias Codex

This repository contains the source data and build scripts for `ai_bias_codex.svg`, an exploratory infographic about where human and AI-related biases can distort human-AI interaction. Please visit [this site](https://littlehifive.github.io/ai-bias-codex/) for an interactive view of the graph.

This infographic is largely inspired by the design of the Cognitive Bias Codex, originally developed by John Manoogian III (jm3) and based on the conceptual organization of biases by Buster Benson. The original visual reference is available on Wikimedia Commons:
[Cognitive Bias Codex](https://commons.wikimedia.org/wiki/File:Cognitive_bias_codex_en.svg).

Unlike cognitive biases, which, thanks in part to Buster Benson's work, have a relatively structured and consolidated presence on Wikipedia, this categorization of biases in human-AI interaction is an exploratory effort by [Zezhen Wu](https://www.linkedin.com/in/zezhenwu/). It extends beyond strictly defined "biases" to organize four broader domains where both AI and human cognitive biases may shape interactions. The structure was assembled through an attempt-to-be-exhaustive synthesis of academic literature together with Wikipedia-based scraping and review assisted by Codex, and is shared as an open, non-canonical resource that the public is invited to fork and refine via GitHub:
[littlehifive/ai-bias-codex](https://github.com/littlehifive/ai-bias-codex).

## What This Is

This codex organizes four broad domains of distortion in human-AI interaction:
- trust and reliance miscalibration: We trust AI too much or too little.
- belief reinforcement and selective uptake: We use AI to confirm what we already believe.
- judgment steering by anchors and frames: AI's suggestions steer our choices.
- mind-perception and capability illusions: We mistake AI for understanding more than it does.

It is not meant as a canonical taxonomy. Unlike cognitive biases, which have a relatively consolidated presence on Wikipedia, this map is an exploratory synthesis that mixes classical cognitive biases, interaction effects, and AI-specific framing concepts when they help explain recurring human-AI failure patterns.

## How The Infographic Was Created

The current build process works in five stages:

1. Define the search space in `data/wikipedia_seed_pages.json`.
2. Scrape one-hop Wikipedia candidates plus curated exact candidates into `data/wikipedia_candidates.json`.
3. Review and cluster accepted pages into wedge-level taxonomy entries in `data/wikipedia_taxonomy_review.json`.
4. Rebuild the render dataset in `data/ai_bias_codex.json`.
5. Fill the original codex SVG template and write `ai_bias_codex.svg`.

The renderer uses `Cognitive_bias_codex_en.svg` as a template so the final output preserves the geometry of the original codex layout while replacing the titles, wedges, labels, links, colors, and footer notes with the AI-bias-specific content from this repository.

## Repo Layout

- `Cognitive_bias_codex_en.svg`: original template used as the structural base for the final render.
- `ai_bias_codex.svg`: generated infographic.
- `data/ai_bias_codex.json`: render-ready dataset for the infographic.
- `data/wikipedia_seed_pages.json`: discovery configuration for seed pages and exact candidates.
- `data/wikipedia_candidates.json`: scraped and deduplicated candidate pages.
- `data/wikipedia_taxonomy_review.json`: reviewed taxonomy, accepted concepts, clustering, and rejection notes.
- `scripts/scrape_wikipedia_candidates.py`: fetches candidate pages from Wikipedia.
- `scripts/rebuild_ai_bias_codex_from_review.py`: converts the reviewed taxonomy into the render-ready dataset.
- `scripts/build_from_template.py`: renders the final SVG from the dataset and template.
- `scripts/generate_ai_bias_codex.py`: validates the dataset and can render a standalone non-template SVG.

## Rebuild

Prerequisites:

- Python 3
- `certifi`

Install the only non-stdlib Python dependency:

```bash
python3 -m pip install certifi
```

Re-scrape candidate pages from the configured seed set:

```bash
python3 scripts/scrape_wikipedia_candidates.py \
  data/wikipedia_seed_pages.json \
  data/wikipedia_candidates.json
```

Rebuild the render dataset from the reviewed taxonomy:

```bash
python3 scripts/rebuild_ai_bias_codex_from_review.py \
  data/wikipedia_taxonomy_review.json \
  data/ai_bias_codex.json
```

That step performs live Wikipedia validation by default. If you need an offline rebuild from already-reviewed data:

```bash
python3 scripts/rebuild_ai_bias_codex_from_review.py \
  --skip-wikipedia-validation \
  data/wikipedia_taxonomy_review.json \
  data/ai_bias_codex.json
```

Render the final infographic:

```bash
python3 scripts/build_from_template.py \
  data/ai_bias_codex.json \
  Cognitive_bias_codex_en.svg \
  ai_bias_codex.svg
```

Optional dataset validation:

```bash
python3 scripts/generate_ai_bias_codex.py data/ai_bias_codex.json --validate-only
```

## Current Snapshot

At the moment, the reviewed taxonomy renders:
- 4 top-level domains
- 20 wedge statements
- 75 linked concepts

The final SVG includes outbound Wikipedia links for the visible concepts plus a footer that records the inspiration and open-resource status of the project.
