#!/usr/bin/env python3

import argparse
import json
import re
import ssl
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import certifi


API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
EXCLUDED_TITLE_PATTERNS = (
    re.compile(r"\(identifier\)$", re.I),
    re.compile(r"\(disambiguation\)$", re.I),
    re.compile(r"^List of ", re.I),
    re.compile(r"^Outline of ", re.I),
)
EXCLUDED_TITLES = {
    "Doi",
    "Digital object identifier",
    "International Standard Book Number",
    "International Standard Serial Number",
}


def fetch_json(params):
    query = urllib.parse.urlencode(params)
    url = f"{API_ENDPOINT}?{query}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ai-bias-codex/1.0 (https://github.com/openai/codex; contact: local-runner)"
        },
    )
    with urllib.request.urlopen(request, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_links(title):
    params = {
        "action": "query",
        "titles": title,
        "prop": "links",
        "plnamespace": 0,
        "pllimit": "max",
        "format": "json",
        "redirects": 1,
    }
    payload = fetch_json(params)
    pages = payload.get("query", {}).get("pages", {})
    page = next(iter(pages.values()))
    links = []
    for link in page.get("links", []):
        link_title = link["title"]
        if any(pattern.search(link_title) for pattern in EXCLUDED_TITLE_PATTERNS):
            continue
        if link_title in EXCLUDED_TITLES:
            continue
        links.append(
            {
                "title": link_title,
                "url": f'https://en.wikipedia.org/wiki/{urllib.parse.quote(link_title.replace(" ", "_"))}',
            }
        )
    return links


def canonical_page(title):
    params = {
        "action": "query",
        "titles": title,
        "format": "json",
        "redirects": 1,
    }
    payload = fetch_json(params)
    pages = payload.get("query", {}).get("pages", {})
    page = next(iter(pages.values()))
    page_title = page.get("title", title)
    return {
        "title": page_title,
        "url": f'https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title.replace(" ", "_"))}',
    }


def load_categories(config):
    if "categories" in config:
        return config["categories"]
    if "seed_pages" in config:
        return [
            {
                "id": "legacy-seed-pages",
                "title": "Legacy seed pages",
                "display_title": "Legacy seed pages",
                "failure_point": "",
                "seed_pages": config["seed_pages"],
            }
        ]
    raise ValueError("Expected either a top-level 'categories' list or a legacy 'seed_pages' list.")


def dedupe_category_links(seed_pages):
    deduped = {}
    for seed in seed_pages:
        for link in seed["links"]:
            candidate = deduped.setdefault(
                link["title"],
                {
                    "title": link["title"],
                    "url": link["url"],
                    "source_seed_titles": [],
                    "source_exact_candidate_titles": [],
                    "source_subcategories": [],
                    "discovery_methods": [],
                },
            )
            if seed["title"] not in candidate["source_seed_titles"]:
                candidate["source_seed_titles"].append(seed["title"])
            subcategory = seed.get("subcategory", "")
            if subcategory and subcategory not in candidate["source_subcategories"]:
                candidate["source_subcategories"].append(subcategory)
            if "linked-from-seed" not in candidate["discovery_methods"]:
                candidate["discovery_methods"].append("linked-from-seed")
    return deduped


def merge_exact_candidates(deduped, exact_candidates):
    for candidate in exact_candidates:
        page = canonical_page(candidate["title"])
        merged = deduped.setdefault(
            page["title"],
            {
                "title": page["title"],
                "url": page["url"],
                "source_seed_titles": [],
                "source_exact_candidate_titles": [],
                "source_subcategories": [],
                "discovery_methods": [],
            },
        )
        if candidate["title"] not in merged["source_exact_candidate_titles"]:
            merged["source_exact_candidate_titles"].append(candidate["title"])
        subcategory = candidate.get("subcategory", "")
        if subcategory and subcategory not in merged["source_subcategories"]:
            merged["source_subcategories"].append(subcategory)
        if "exact-candidate" not in merged["discovery_methods"]:
            merged["discovery_methods"].append("exact-candidate")
    return sorted(
        deduped.values(),
        key=lambda item: (
            -len(item["source_seed_titles"]) - len(item["source_exact_candidate_titles"]),
            item["title"].lower(),
        ),
    )


def main():
    parser = argparse.ArgumentParser(description="Scrape direct Wikipedia links for the configured seed pages.")
    parser.add_argument("seed_file", type=Path, help="Path to wikipedia_seed_pages.json.")
    parser.add_argument("output", type=Path, help="Path for the scraped candidate JSON.")
    args = parser.parse_args()

    config = json.loads(args.seed_file.read_text())
    categories = load_categories(config)
    scraped_categories = []
    global_candidates = defaultdict(set)
    total_seed_pages = 0

    for category in categories:
        scraped_seed_pages = []
        scraped_exact_candidates = []
        seed_link_sets = []
        for seed in category["seed_pages"]:
            links = fetch_links(seed["title"])
            total_seed_pages += 1
            seed_link_sets.append(
                {
                    "title": seed["title"],
                    "subcategory": seed.get("subcategory", ""),
                    "links": links,
                }
            )
            scraped_seed_pages.append(
                {
                    "title": seed["title"],
                    "url": seed["url"],
                    "subcategory": seed.get("subcategory", ""),
                    "note": seed.get("note", ""),
                    "link_count": len(links),
                }
            )
            for link in links:
                global_candidates[link["title"]].add(category["title"])

        for exact in category.get("exact_candidates", []):
            page = canonical_page(exact["title"])
            scraped_exact_candidates.append(
                {
                    "title": page["title"],
                    "url": page["url"],
                    "requested_title": exact["title"],
                    "subcategory": exact.get("subcategory", ""),
                    "note": exact.get("note", ""),
                }
            )
            global_candidates[page["title"]].add(category["title"])

        candidate_pages = dedupe_category_links(seed_link_sets)
        candidate_pages = merge_exact_candidates(candidate_pages, category.get("exact_candidates", []))
        scraped_categories.append(
            {
                "id": category.get("id", ""),
                "title": category["title"],
                "display_title": category.get("display_title", category["title"]),
                "failure_point": category.get("failure_point", ""),
                "seed_pages": scraped_seed_pages,
                "exact_candidates": scraped_exact_candidates,
                "candidate_pages": candidate_pages,
                "seed_page_count": len(scraped_seed_pages),
                "exact_candidate_count": len(scraped_exact_candidates),
                "candidate_count": len(candidate_pages),
            }
        )

    payload = {
        "mission": config.get("mission", ""),
        "categories": scraped_categories,
        "summary": {
            "category_count": len(scraped_categories),
            "seed_page_count": total_seed_pages,
            "unique_candidate_count": len(global_candidates),
        },
    }

    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
