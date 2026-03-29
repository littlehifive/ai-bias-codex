#!/usr/bin/env python3

import argparse
import json
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

import certifi


API_ENDPOINT = "https://en.wikipedia.org/w/api.php"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


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
        links.append(
            {
                "title": link_title,
                "url": f'https://en.wikipedia.org/wiki/{urllib.parse.quote(link_title.replace(" ", "_"))}',
            }
        )
    return links


def main():
    parser = argparse.ArgumentParser(description="Scrape direct Wikipedia links for the configured seed pages.")
    parser.add_argument("seed_file", type=Path, help="Path to wikipedia_seed_pages.json.")
    parser.add_argument("output", type=Path, help="Path for the scraped candidate JSON.")
    args = parser.parse_args()

    config = json.loads(args.seed_file.read_text())
    scraped = []
    for seed in config["seed_pages"]:
        links = fetch_links(seed["title"])
        scraped.append(
            {
                "title": seed["title"],
                "url": seed["url"],
                "note": seed.get("note", ""),
                "links": links,
            }
        )

    args.output.write_text(json.dumps({"seed_pages": scraped}, indent=2, sort_keys=True))
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
