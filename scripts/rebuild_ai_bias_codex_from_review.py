#!/usr/bin/env python3

import argparse
import json
import re
import ssl
from pathlib import Path
from urllib.parse import urlencode, urlsplit, unquote
from urllib.request import Request, urlopen

import certifi


DEFAULT_COLORS = {
    "Trust and Reliance Miscalibration": "#1f6fa8",
    "Belief Reinforcement and Selective Uptake": "#7c7c7c",
    "Judgment Steering by Anchors and Frames": "#0a8f83",
    "Mind-Perception and Capability Illusions": "#5d8b1a",
}
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
ACCEPTED_STATUSES = {"accepted-leaf", "accepted-support"}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def wikipedia_api_get(**params):
    query = urlencode(params)
    request = Request(f"{WIKIPEDIA_API}?{query}", headers={"User-Agent": "ai-bias-codex/1.0"})
    context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(request, timeout=30, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_review_pages(review):
    seen = set()
    for category in review["recommended_codex_structure"]:
        for wedge in category["wedges"]:
            for page in wedge["pages"]:
                key = (page["wikipedia_url"], page.get("link_kind", "exact"))
                if key not in seen:
                    seen.add(key)
                    yield page
    for page in review.get("candidate_inventory", []):
        if page.get("status") not in ACCEPTED_STATUSES:
            continue
        key = (page["wikipedia_url"], page.get("link_kind", "exact"))
        if key not in seen:
            seen.add(key)
            yield page


def canonical_display_label(page):
    return page.get("display_label", page["wikipedia_page_title"])


def parse_wikipedia_url(url):
    parts = urlsplit(url)
    title = unquote(parts.path.rsplit("/", 1)[-1]).replace("_", " ")
    anchor = unquote(parts.fragment)
    return title, anchor


def validate_exact_pages(pages):
    title_to_pages = {}
    for page in pages:
        title, _ = parse_wikipedia_url(page["wikipedia_url"])
        title_to_pages.setdefault(title, []).append(page)

    errors = []
    for title_batch in chunked(sorted(title_to_pages), 50):
        payload = wikipedia_api_get(action="query", titles="|".join(title_batch), redirects=1, format="json")
        for result in payload["query"]["pages"].values():
            if "missing" in result or "invalid" in result:
                missing_title = result.get("title") or "<unknown>"
                for page in title_to_pages.get(missing_title, []):
                    errors.append(f'Missing Wikipedia page for "{page["wikipedia_page_title"]}" -> {page["wikipedia_url"]}')

    return errors


def validate_section_pages(pages):
    errors = []
    for page in pages:
        title, anchor = parse_wikipedia_url(page["wikipedia_url"])
        payload = wikipedia_api_get(action="parse", page=title, prop="sections", format="json")
        if "error" in payload:
            errors.append(f'Missing Wikipedia page for section link "{page["wikipedia_url"]}".')
            continue
        anchors = {section["anchor"]: section["line"] for section in payload["parse"].get("sections", [])}
        if anchor not in anchors:
            errors.append(f'Missing Wikipedia section "#{anchor}" for "{title}".')
            continue
        if canonical_display_label(page) != anchors[anchor]:
            errors.append(
                f'Display label "{canonical_display_label(page)}" does not match Wikipedia section title "{anchors[anchor]}".'
            )
    return errors


def validate_review(review):
    exact_pages = []
    section_pages = []
    for page in iter_review_pages(review):
        if page.get("link_kind", "exact") == "section":
            section_pages.append(page)
        else:
            exact_pages.append(page)

    errors = validate_exact_pages(exact_pages)
    errors.extend(validate_section_pages(section_pages))
    if errors:
        raise SystemExit("Wikipedia reference validation failed:\n- " + "\n- ".join(sorted(set(errors))))


def build_leaf(quadrant_title, statement_label, page):
    return {
        "quadrant": quadrant_title,
        "statement": statement_label,
        "bias_name": page["wikipedia_page_title"],
        "display_label": canonical_display_label(page),
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
    parser.add_argument(
        "--skip-wikipedia-validation",
        action="store_true",
        help="Skip live validation that accepted pages and labels map to Wikipedia pages or section titles.",
    )
    args = parser.parse_args()

    review = json.loads(args.review.read_text())
    if not args.skip_wikipedia_validation:
        validate_review(review)
    dataset = build_dataset(review)
    args.output.write_text(json.dumps(dataset, indent=2, ensure_ascii=True) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
