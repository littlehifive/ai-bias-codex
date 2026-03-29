#!/usr/bin/env python3

import argparse
import json
import math
import textwrap
from collections import Counter
from html import escape
from pathlib import Path


REQUIRED_LEAF_FIELDS = (
    "quadrant",
    "statement",
    "bias_name",
    "one_sentence_definition",
    "interaction_rationale",
    "wikipedia_url",
    "link_kind",
    "seed_page",
    "review_status",
)
VALID_LINK_KINDS = {"exact", "section", "proxy"}
DISPLAY_LABEL_OVERRIDES = {
    "AI anthropomorphism": "AI anthropomorphism",
    "Anthropomorphism": "Anthropomorphism",
    "Authority bias": "Authority bias",
    "Belief perseverance": "Belief perseverance",
    "Choice architecture": "Choice architecture",
    "Mere-exposure effect": "Mere exposure",
    "Illusory truth effect": "Illusory truth",
    "Hallucination (artificial intelligence)": "AI hallucination",
    "Computers are social actors": "CASA",
    "Credibility": "Credibility",
    "Social presence theory": "Social presence",
    "Echo chamber (media)": "Echo chamber",
    "Argument from authority": "Authority argument",
    "Explainable artificial intelligence": "Explainable AI",
    "Algorithm appreciation": "Algorithm appreciation",
    "Out-of-the-loop performance problem": "Out-of-the-loop problem",
    "False consensus effect": "False consensus",
    "Fairness (machine learning)": "ML fairness",
    "Fluency heuristic": "Fluency heuristic",
    "Framing effect (psychology)": "Framing effect",
    "Illusion of explanatory depth": "Explanatory depth",
    "Identifiable victim effect": "Identifiable victim",
    "Reactance (psychology)": "Reactance",
    "Selective exposure theory": "Selective exposure",
    "Recommender system": "Recommender systems",
    "Source-monitoring error": "Source monitoring",
    "Trust (social science)": "Trust",
}


def polar(cx, cy, radius, angle_deg):
    radians = math.radians(angle_deg)
    x = cx + radius * math.sin(radians)
    y = cy - radius * math.cos(radians)
    return x, y


def donut_sector_path(cx, cy, inner_radius, outer_radius, start_angle, end_angle):
    start_outer = polar(cx, cy, outer_radius, start_angle)
    end_outer = polar(cx, cy, outer_radius, end_angle)
    start_inner = polar(cx, cy, inner_radius, start_angle)
    end_inner = polar(cx, cy, inner_radius, end_angle)
    large_arc = 1 if (end_angle - start_angle) > 180 else 0
    return (
        f"M {start_outer[0]:.1f} {start_outer[1]:.1f} "
        f"A {outer_radius:.1f} {outer_radius:.1f} 0 {large_arc} 1 {end_outer[0]:.1f} {end_outer[1]:.1f} "
        f"L {end_inner[0]:.1f} {end_inner[1]:.1f} "
        f"A {inner_radius:.1f} {inner_radius:.1f} 0 {large_arc} 0 {start_inner[0]:.1f} {start_inner[1]:.1f} Z"
    )


def wrap_lines(text, width):
    lines = textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=True)
    return lines or [text]


def tspan_block(lines, x, first_dy, line_height):
    parts = []
    for index, line in enumerate(lines):
        dy = first_dy if index == 0 else line_height
        parts.append(f'<tspan x="{x}" dy="{dy}">{escape(line)}</tspan>')
    return "".join(parts)


def render_multiline_text(x, y, lines, anchor, font_size, fill, weight=400, rotate=None):
    line_height = round(font_size * 1.18, 1)
    first_dy = -(line_height * (len(lines) - 1)) / 2
    transform = f' transform="rotate({rotate:.1f} {x:.1f} {y:.1f})"' if rotate is not None else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-size="{font_size:.1f}" font-weight="{weight}" fill="{fill}"{transform}>'
        f'{tspan_block(lines, f"{x:.1f}", f"{first_dy:.1f}", f"{line_height:.1f}")}</text>'
    )


def curve_between(cx, cy, start_radius, start_angle, end_radius, end_angle):
    start_x, start_y = polar(cx, cy, start_radius, start_angle)
    end_x, end_y = polar(cx, cy, end_radius, end_angle)
    c1_x, c1_y = polar(cx, cy, start_radius + (end_radius - start_radius) * 0.45, start_angle)
    c2_x, c2_y = polar(cx, cy, start_radius + (end_radius - start_radius) * 0.82, end_angle)
    return (
        f"M {start_x:.1f} {start_y:.1f} "
        f"C {c1_x:.1f} {c1_y:.1f}, {c2_x:.1f} {c2_y:.1f}, {end_x:.1f} {end_y:.1f}"
    )


def leaf_display_label(leaf):
    return DISPLAY_LABEL_OVERRIDES.get(leaf["bias_name"], leaf["bias_name"])


def iter_statements(dataset):
    for quadrant_index, quadrant in enumerate(dataset["quadrants"]):
        for statement_index, statement in enumerate(quadrant["statements"]):
            yield quadrant_index, quadrant, statement_index, statement


def iter_leaves(dataset):
    for quadrant_index, quadrant, statement_index, statement in iter_statements(dataset):
        for leaf_index, leaf in enumerate(statement["leaves"]):
            yield quadrant_index, quadrant, statement_index, statement, leaf_index, leaf


def validate_dataset(dataset):
    errors = []
    quadrants = dataset.get("quadrants", [])
    if len(quadrants) != 4:
        errors.append(f"Expected 4 quadrants, found {len(quadrants)}.")

    statement_count = 0
    seen_names = set()
    for quadrant in quadrants:
        statements = quadrant.get("statements", [])
        statement_count += len(statements)
        if len(statements) != 5:
            errors.append(
                f'Quadrant "{quadrant.get("title", "<missing>")}" should have 5 statements, found {len(statements)}.'
            )
        for statement in statements:
            leaves = statement.get("leaves", [])
            if len(leaves) < 2:
                errors.append(
                    f'Statement "{statement.get("label", "<missing>")}" should have at least 2 leaves, found {len(leaves)}.'
                )
            for leaf in leaves:
                for field in REQUIRED_LEAF_FIELDS:
                    if field not in leaf or str(leaf[field]).strip() == "":
                        errors.append(f'Missing "{field}" on leaf "{leaf.get("bias_name", "<missing>")}".')
                if leaf.get("link_kind") not in VALID_LINK_KINDS:
                    errors.append(
                        f'Invalid link_kind "{leaf.get("link_kind")}" on leaf "{leaf.get("bias_name", "<missing>")}".'
                    )
                if leaf.get("quadrant") != quadrant.get("title"):
                    errors.append(
                        f'Leaf "{leaf.get("bias_name", "<missing>")}" has quadrant "{leaf.get("quadrant")}" '
                        f'but is nested under "{quadrant.get("title")}".'
                    )
                if leaf.get("statement") != statement.get("label"):
                    errors.append(
                        f'Leaf "{leaf.get("bias_name", "<missing>")}" has statement "{leaf.get("statement")}" '
                        f'but is nested under "{statement.get("label")}".'
                    )
                bias_name = leaf.get("bias_name")
                if bias_name in seen_names:
                    errors.append(f'Duplicate bias_name "{bias_name}".')
                seen_names.add(bias_name)

    if statement_count != 20:
        errors.append(f"Expected 20 statements, found {statement_count}.")
    return errors


def dataset_summary(dataset):
    link_kinds = Counter()
    total_leaves = 0
    for _, _, _, _, _, leaf in iter_leaves(dataset):
        total_leaves += 1
        link_kinds[leaf["link_kind"]] += 1
    return {
        "quadrants": len(dataset["quadrants"]),
        "statements": sum(len(quadrant["statements"]) for quadrant in dataset["quadrants"]),
        "leaves": total_leaves,
        "link_kinds": dict(link_kinds),
    }


def render_svg(dataset):
    width = 2800
    height = 1800
    cx = width / 2
    cy = 930
    background = "#f6f1e8"
    center_circle = 190
    branch_origin_radius = 220
    cluster_root_radius = 365
    leaf_dot_radius = 545
    statement_dot_radius = 720
    guide_circle = 745
    title_color = "#191919"
    text_color = "#232323"
    muted = "#6b6b67"
    grid = "#d4d0c9"
    summary = dataset_summary(dataset)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(dataset["title"])}</title>',
        f'<desc id="desc">{escape(dataset["subtitle"])}</desc>',
        "<style>",
        "text { font-family: Georgia, 'Times New Roman', serif; }",
        "a { text-decoration: none; }",
        ".leaf:hover text { fill: #000; }",
        ".leaf:hover circle { r: 4.5; }",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="{background}"/>',
    ]

    for quadrant_index, quadrant in enumerate(dataset["quadrants"]):
        quadrant_start = quadrant_index * 90
        quadrant_end = quadrant_start + 90
        parts.append(
            f'<path d="{donut_sector_path(cx, cy, center_circle + 55, guide_circle + 135, quadrant_start, quadrant_end)}" '
            f'fill="{quadrant["color"]}" opacity="0.08" stroke="{quadrant["color"]}" stroke-width="0.8"/>'
        )
        title_angle = quadrant_start + 45
        title_x, title_y = polar(cx, cy, 1045, title_angle)
        title_lines = wrap_lines(quadrant["title"], 18)
        parts.append(render_multiline_text(title_x, title_y, title_lines, "middle", 33, quadrant["color"], 700))

    parts.append(
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{guide_circle:.1f}" fill="none" stroke="{grid}" stroke-width="1.6"/>'
    )
    parts.append(
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{center_circle:.1f}" fill="{background}" stroke="{grid}" stroke-width="1.6"/>'
    )

    title_lines = wrap_lines(dataset["title"], 24)
    parts.append(render_multiline_text(cx, 30, title_lines, "middle", 28.5, title_color, 700))

    parts.append(render_multiline_text(cx, cy - 12, ["Human-AI interaction"], "middle", 20, title_color, 600))
    parts.append(render_multiline_text(cx, cy + 30, ["bias map"], "middle", 20, title_color, 600))
    parts.append(
        f'<text x="{cx:.1f}" y="{cy + 98:.1f}" text-anchor="middle" fill="{muted}" font-size="16">'
        f'{summary["leaves"]} linked concepts across {summary["statements"]} statements</text>'
    )

    for quadrant_index, quadrant, statement_index, statement in iter_statements(dataset):
        statement_start = quadrant_index * 90 + statement_index * 18
        statement_end = statement_start + 18
        statement_mid = (statement_start + statement_end) / 2
        statement_x, statement_y = polar(cx, cy, statement_dot_radius, statement_mid)
        label_x, label_y = polar(cx, cy, 820, statement_mid)
        cluster_root_x, cluster_root_y = polar(cx, cy, cluster_root_radius, statement_mid)
        center_anchor_x, center_anchor_y = polar(cx, cy, branch_origin_radius, statement_mid)
        anchor = "start" if label_x >= cx else "end"
        if 172 <= statement_mid <= 188:
            anchor = "middle"
        if statement_mid <= 8 or statement_mid >= 352:
            anchor = "middle"
            label_y += 32
        label_offset = 36 if anchor == "start" else -36 if anchor == "end" else 0
        line_end_x = label_x - 14 if anchor == "start" else label_x + 14 if anchor == "end" else label_x
        statement_lines = wrap_lines(statement["label"], 29)
        text_x = label_x + label_offset
        if anchor == "start":
            text_x = min(width - 340, text_x)
        elif anchor == "end":
            text_x = max(340, text_x)
        parts.append(
            f'<path d="{curve_between(cx, cy, branch_origin_radius, statement_mid, cluster_root_radius, statement_mid)}" '
            f'stroke="{quadrant["color"]}" stroke-width="1.5" opacity="0.65" fill="none"/>'
        )
        parts.append(
            f'<path d="{curve_between(cx, cy, cluster_root_radius, statement_mid, statement_dot_radius, statement_mid)}" '
            f'stroke="{quadrant["color"]}" stroke-width="1.35" opacity="0.70" fill="none"/>'
        )
        parts.append(
            f'<line x1="{statement_x:.1f}" y1="{statement_y:.1f}" x2="{line_end_x:.1f}" y2="{label_y:.1f}" '
            f'stroke="{quadrant["color"]}" stroke-width="1.4" opacity="0.55"/>'
        )
        parts.append(
            f'<circle cx="{statement_x:.1f}" cy="{statement_y:.1f}" r="9" fill="{quadrant["color"]}" opacity="0.95"/>'
        )
        parts.append(
            render_multiline_text(
                text_x,
                label_y,
                statement_lines,
                anchor,
                18,
                quadrant["color"],
                600,
            )
        )

        leaf_count = len(statement["leaves"])
        for leaf_index, leaf in enumerate(statement["leaves"]):
            leaf_span = 14
            angle = statement_mid - (leaf_span / 2) + ((leaf_index + 0.5) * (leaf_span / leaf_count))
            dot_x, dot_y = polar(cx, cy, leaf_dot_radius, angle)
            label_rotation = angle if angle <= 180 else angle - 180
            text_x = 12 if angle <= 180 else -12
            anchor = "start" if angle <= 180 else "end"
            display_label = leaf_display_label(leaf)
            leaf_lines = wrap_lines(display_label, 22)
            line_height = 13.2
            first_dy = -(line_height * (len(leaf_lines) - 1)) / 2
            tooltip = (
                f'{leaf["bias_name"]}\n'
                f'{leaf["one_sentence_definition"]}\n'
                f'AI interaction: {leaf["interaction_rationale"]}\n'
                f'Link type: {leaf["link_kind"]}\n'
                f'Seed page: {leaf["seed_page"]}'
            )
            parts.append(
                f'<path d="{curve_between(cx, cy, cluster_root_radius, statement_mid, leaf_dot_radius, angle)}" '
                f'stroke="{quadrant["color"]}" stroke-width="1.1" opacity="0.70" fill="none"/>'
            )
            parts.append(
                f'<a class="leaf" xlink:href="{escape(leaf["wikipedia_url"], quote=True)}" target="_blank">'
                f'<title>{escape(tooltip)}</title>'
                f'<g transform="translate({dot_x:.1f} {dot_y:.1f}) rotate({label_rotation:.1f})">'
                f'<circle cx="0" cy="0" r="3.2" fill="{quadrant["color"]}"/>'
                f'<text x="{text_x}" y="0" text-anchor="{anchor}" font-size="10.8" font-weight="500" fill="{quadrant["color"]}">'
                f'{tspan_block(leaf_lines, text_x, f"{first_dy:.1f}", f"{line_height:.1f}")}'
                f"</text></g></a>"
            )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Generate the AI Bias Codex SVG from curated JSON data.")
    parser.add_argument("dataset", type=Path, help="Path to the curated dataset JSON file.")
    parser.add_argument("output", type=Path, nargs="?", help="Output SVG path.")
    parser.add_argument("--validate-only", action="store_true", help="Validate the dataset and exit.")
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text())
    errors = validate_dataset(dataset)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)

    summary = dataset_summary(dataset)
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.validate_only:
        return
    if args.output is None:
        raise SystemExit("An output SVG path is required unless --validate-only is set.")

    svg = render_svg(dataset)
    args.output.write_text(svg)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
