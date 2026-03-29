#!/usr/bin/env python3

import argparse
import json
import math
import re
import textwrap
from html import escape
from pathlib import Path


DISPLAY_LABEL_OVERRIDES = {
    "AI anthropomorphism": "AI anthropomorphism",
    "Hallucination (artificial intelligence)": "AI hallucination",
    "Framing effect (psychology)": "Framing effect",
    "Computers are social actors": "CASA",
    "Social presence theory": "Social presence",
    "Recommender system": "Recommender system",
    "Echo chamber (media)": "Echo chamber",
    "Explainable artificial intelligence": "Explainable AI",
    "False consensus effect": "False consensus",
    "Fluency heuristic": "Fluency heuristic",
    "Illusion of explanatory depth": "Explanatory depth",
    "Identifiable victim effect": "Identifiable victim",
    "Intentional stance": "Intentional stance",
    "Mind projection fallacy": "Mind projection",
    "Algorithm appreciation": "Algorithm appreciation",
    "Automation misuse": "Automation misuse",
    "Out-of-the-loop performance problem": "Out-of-the-loop problem",
    "Automation complacency": "Automation complacency",
    "Law of the instrument": "Law of instrument",
    "Escalation of commitment": "Escalation of commitment",
    "Reactance (psychology)": "Reactance",
    "Selective exposure theory": "Selective exposure",
    "Trust (social science)": "Trust",
    "Fairness (machine learning)": "ML fairness",
    "Source-monitoring error": "Source monitoring",
    "Targeted advertising": "Targeted ads",
    "Argument from authority": "Authority argument",
}
QUADRANT_LINE_HEIGHT = 34.0
TITLE_LINE_HEIGHT = 38.0

TITLE_ID = "trsvg248"
QUADRANT_IDS = ["trsvg249", "trsvg250", "trsvg251", "trsvg252"]
STATEMENT_IDS = [
    "trsvg265",
    "trsvg272",
    "trsvg281",
    "trsvg295",
    "trsvg299",
    "trsvg313",
    "trsvg326",
    "trsvg336",
    "trsvg346",
    "trsvg353",
    "trsvg368",
    "trsvg390",
    "trsvg394",
    "trsvg408",
    "trsvg415",
    "trsvg425",
    "trsvg432",
    "trsvg439",
    "trsvg453",
    "trsvg460",
]
GROUP_PATTERN = re.compile(
    r"(<g>\n(?P<body>.*?)<circle cx=\"(?P<cx>[-0-9.]+)\" cy=\"(?P<cy>[-0-9.]+)\" r=\"10\.0\"/>\n"
    r"<switch style=\"font-size:15\.0px;\">.*?<text[^>]*id=\"(?P<id>trsvg\d+)\".*?</switch>\n</g>)",
    re.S,
)
ANCHOR_PATTERN = re.compile(r"<a xlink:href=\"https://en\.wikipedia\.org/wiki/[^\"]+\">.*?</a>", re.S)


def wrap_lines(text, width):
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=True) or [text]


def display_label(leaf):
    if leaf.get("display_label"):
        return leaf["display_label"]
    return DISPLAY_LABEL_OVERRIDES.get(leaf["bias_name"], leaf["bias_name"])


def replace_text_block(svg_text, text_id, lines):
    pattern = re.compile(rf'(<text[^>]*id="{text_id}"[^>]*>)(.*?)(</text>)', re.S)
    match = pattern.search(svg_text)
    if not match:
        raise ValueError(f"Unable to find English text block for {text_id}.")

    open_tag, _, close_tag = match.groups()
    if "x=" in open_tag:
        x_match = re.search(r'x=\"([^\"]+)\"', open_tag)
        x_value = x_match.group(1)
        first_y = 4 - 10.8 * (len(lines) - 1)
        tspans = []
        for index, line in enumerate(lines):
            if index == 0:
                tspans.append(f'<tspan x="{x_value}" y="{first_y:.1f}">{escape(line)}</tspan>')
            else:
                tspans.append(f'<tspan x="{x_value}" dy="12.0">{escape(line)}</tspan>')
        replacement = open_tag + "".join(tspans) + close_tag
    elif "y=" in open_tag:
        y_match = re.search(r'y=\"([^\"]+)\"', open_tag)
        base_y = float(y_match.group(1))
        first_y = base_y - ((len(lines) - 1) * TITLE_LINE_HEIGHT) / 2
        tspans = []
        for index, line in enumerate(lines):
            if index == 0:
                tspans.append(f'<tspan x="0" y="{first_y:.1f}">{escape(line)}</tspan>')
            else:
                tspans.append(f'<tspan x="0" dy="{TITLE_LINE_HEIGHT:.1f}">{escape(line)}</tspan>')
        replacement = open_tag + "".join(tspans) + close_tag
    else:
        line_height = QUADRANT_LINE_HEIGHT if text_id in QUADRANT_IDS else 22.5
        first_y = -((len(lines) - 1) * line_height) / 2
        tspans = []
        for index, line in enumerate(lines):
            if index == 0:
                tspans.append(f'<tspan x="0" y="{first_y:.1f}">{escape(line)}</tspan>')
            else:
                tspans.append(f'<tspan x="0" dy="{line_height:.1f}">{escape(line)}</tspan>')
        replacement = open_tag + "".join(tspans) + close_tag

    return svg_text[: match.start()] + replacement + svg_text[match.end() :]


def evenly_spaced_indices(total_slots, used_slots):
    if used_slots >= total_slots:
        return list(range(total_slots))
    picks = []
    used = set()
    for index in range(used_slots):
        raw = ((index + 0.5) * total_slots / used_slots) - 0.5
        candidate = int(round(raw))
        candidate = max(0, min(total_slots - 1, candidate))
        while candidate in used and candidate + 1 < total_slots:
            candidate += 1
        while candidate in used and candidate - 1 >= 0:
            candidate -= 1
        used.add(candidate)
        picks.append(candidate)
    return sorted(picks)


def rewrite_leaf_anchor(anchor_block, leaf=None, hide=False):
    if hide:
        return anchor_block.replace("<a ", '<a style="display:none" ', 1)

    href_match = re.search(r'<a xlink:href=\"([^\"]+)\"', anchor_block)
    if not href_match:
        raise ValueError("Anchor block missing href.")
    updated = anchor_block.replace(href_match.group(1), leaf["wikipedia_url"], 1)

    text_match = re.search(r'<text[^>]*id="(trsvg\d+)"[^>]*>(.*?)</text>', updated, re.S)
    if not text_match:
        raise ValueError(f'Unable to find English leaf text for {leaf["bias_name"]}.')
    text_id = text_match.group(1)
    label = display_label(leaf)
    label_lines = wrap_lines(label, 20)
    updated = replace_text_block(updated, text_id, label_lines)

    return updated


def quadrant_lines(title):
    return wrap_lines(title, 18)


def statement_lines(label):
    return wrap_lines(label, 34)


def title_lines():
    return ["The Human-AI Interaction", "Bias Codex"]


def main():
    parser = argparse.ArgumentParser(description="Fill the original cognitive bias codex SVG template with AI-bias content.")
    parser.add_argument("dataset", type=Path, help="Curated AI bias dataset JSON.")
    parser.add_argument("template", type=Path, help="Original SVG template path.")
    parser.add_argument("output", type=Path, help="Output SVG path.")
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text())
    svg = args.template.read_text()

    svg = replace_text_block(svg, TITLE_ID, title_lines())

    quadrants_clockwise = [
        dataset["quadrants"][0]["title"],
        dataset["quadrants"][1]["title"],
        dataset["quadrants"][2]["title"],
        dataset["quadrants"][3]["title"],
    ]
    for text_id, title in zip(QUADRANT_IDS, quadrants_clockwise):
        svg = replace_text_block(svg, text_id, quadrant_lines(title))

    statements = []
    for quadrant in dataset["quadrants"]:
        statements.extend(quadrant["statements"])
    for text_id, statement in zip(STATEMENT_IDS, statements):
        svg = replace_text_block(svg, text_id, statement_lines(statement["label"]))

    groups = list(GROUP_PATTERN.finditer(svg))
    if len(groups) != 20:
        raise ValueError(f"Expected 20 statement groups in template, found {len(groups)}.")

    rebuilt = []
    cursor = 0
    visible_leaves = 0
    omitted = []
    for group_index, match in enumerate(groups):
        rebuilt.append(svg[cursor : match.start()])
        whole_group = match.group(1)
        body = match.group("body")
        statement = statements[group_index]
        anchors = ANCHOR_PATTERN.findall(body)
        renderable = min(len(anchors), len(statement["leaves"]))
        selected = evenly_spaced_indices(len(anchors), renderable)
        selected_map = dict(zip(selected, statement["leaves"][:renderable]))
        visible_leaves += renderable
        if len(statement["leaves"]) > len(anchors):
            omitted.extend(leaf["bias_name"] for leaf in statement["leaves"][len(anchors) :])
        updated_anchors = []
        for anchor_index, anchor_block in enumerate(anchors):
            if anchor_index in selected_map:
                updated_anchors.append(rewrite_leaf_anchor(anchor_block, selected_map[anchor_index], hide=False))
            else:
                updated_anchors.append(rewrite_leaf_anchor(anchor_block, hide=True))
        new_body = ANCHOR_PATTERN.sub(lambda _: updated_anchors.pop(0), body)
        rebuilt.append(whole_group.replace(body, new_body, 1))
        cursor = match.end()
    rebuilt.append(svg[cursor:])

    args.output.write_text("".join(rebuilt))
    print(f"Wrote {args.output}")
    print(f"Visible leaves: {visible_leaves}")
    if omitted:
        print("Omitted due to template slot limits:")
        for name in omitted:
            print(f"- {name}")


if __name__ == "__main__":
    main()
