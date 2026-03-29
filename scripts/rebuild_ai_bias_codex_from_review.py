#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


DEFAULT_COLORS = {
    "Trust and Reliance Miscalibration": "#1f6fa8",
    "Belief Reinforcement and Selective Uptake": "#7c7c7c",
    "Judgment Steering by Anchors and Frames": "#0a8f83",
    "Mind-Perception and Capability Illusions": "#5d8b1a",
}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_leaf(quadrant_title, statement_label, page):
    return {
        "quadrant": quadrant_title,
        "statement": statement_label,
        "bias_name": page["wikipedia_page_title"],
        "display_label": page.get("display_label", page["wikipedia_page_title"]),
        "one_sentence_definition": page["one_sentence_definition"],
        "interaction_rationale": page["why_it_fits"],
        "wikipedia_url": page["wikipedia_url"],
        "link_kind": page.get("link_kind", "exact"),
        "seed_page": page.get("seed_page", page["wikipedia_page_title"]),
        "review_status": page["status"],
        "research_subcategory": page["subcategory"],
        "cross_links": page.get("cross_links", []),
        "render_priority": page.get("render_priority", 1),
    }


def build_dataset(review):
    quadrants = []
    for category in review["recommended_codex_structure"]:
        statements = []
        for wedge in category["wedges"]:
            label = wedge["public_label"]
            ordered_pages = sorted(wedge["pages"], key=lambda page: page.get("render_priority", 1))
            statements.append(
                {
                    "id": wedge.get("id", slugify(wedge["research_subcategory"])),
                    "label": label,
                    "research_subcategory": wedge["research_subcategory"],
                    "leaves": [build_leaf(category["public_label"], label, page) for page in ordered_pages],
                }
            )

        quadrants.append(
            {
                "id": category.get("id", slugify(category["top_level_category"])),
                "title": category["public_label"],
                "research_title": category["top_level_category"],
                "failure_point": category["failure_point"],
                "color": category.get("color", DEFAULT_COLORS[category["top_level_category"]]),
                "statements": statements,
            }
        )

    return {
        "title": review.get("title", "The Human-AI Interaction Bias Codex"),
        "subtitle": review.get(
            "subtitle",
            "A Wikipedia-backed map of human judgment distortions in human-AI interaction.",
        ),
        "taxonomy_source": "data/wikipedia_taxonomy_review.json",
        "quadrants": quadrants,
    }


def main():
    parser = argparse.ArgumentParser(description="Build the infographic dataset from the reviewed Wikipedia taxonomy.")
    parser.add_argument("review", type=Path, help="Path to wikipedia_taxonomy_review.json.")
    parser.add_argument("output", type=Path, help="Path to ai_bias_codex.json.")
    args = parser.parse_args()

    review = json.loads(args.review.read_text())
    dataset = build_dataset(review)
    args.output.write_text(json.dumps(dataset, indent=2, ensure_ascii=True) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
