#!/usr/bin/env python3

import argparse
import json
import math
import re
import textwrap
from html import escape
from pathlib import Path


DISPLAY_LABEL_OVERRIDES = {}
QUADRANT_LINE_HEIGHT = 34.0
TITLE_LINE_HEIGHT = 42.0
TITLE_FONT_SIZE = 40.0
TITLE_Y = -720.0
FOOTER_TEXT_COLOR = "#5f5f5f"
FOOTER_FONT_SIZE = 11.0
FOOTER_LEFT_X = 110
FOOTER_START_Y = 1510
FOOTER_LINE_HEIGHT = 13
EXPANDED_CANVAS_HEIGHT = 1620

TITLE_ID = "trsvg248"
QUADRANT_IDS = ["trsvg249", "trsvg250", "trsvg251", "trsvg252"]
TEMPLATE_QUADRANT_COLORS = ["#098", "#07A", "#490", "#888"]
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
        if text_id == TITLE_ID:
            open_tag = re.sub(r'font-size:[0-9.]+px;', f'font-size:{TITLE_FONT_SIZE:.1f}px;', open_tag)
            open_tag = re.sub(r'y=\"[^\"]+\"', f'y="{TITLE_Y:.1f}"', open_tag)
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
    return ["THE HUMAN-AI INTERACTION", "BIAS CODEX"]


def apply_quadrant_colors(svg_text, quadrant_colors):
    updated = svg_text
    for template_color, color in zip(TEMPLATE_QUADRANT_COLORS, quadrant_colors):
        updated = updated.replace(template_color, color)
    return updated


def apply_statement_text_colors(svg_text, quadrant_colors):
    updated = svg_text
    for index, text_id in enumerate(STATEMENT_IDS):
        color = quadrant_colors[index // 5]
        pattern = re.compile(rf'(<text[^>]*id="{text_id}"[^>]*)(>)')
        updated, count = pattern.subn(
            lambda match: (
                re.sub(r'fill=\"[^\"]*\"', f'fill="{color}"', match.group(1))
                if "fill=" in match.group(1)
                else match.group(1) + f' fill="{color}"'
            )
            + match.group(2),
            updated,
            count=1,
        )
        if count == 0:
            raise ValueError(f"Unable to find statement text block for {text_id}.")
    return updated


def footer_notes_svg():
    footer = [
        '<g id="footer-notes">',
        (
            f'<text x="{FOOTER_LEFT_X}" y="{FOOTER_START_Y}" fill="{FOOTER_TEXT_COLOR}" '
            f'font-size="{FOOTER_FONT_SIZE:.1f}px" font-weight="600">Notes</text>'
        ),
    ]
    y = FOOTER_START_Y + FOOTER_LINE_HEIGHT
    rendered_lines = [
        [
            ('1. This infographic is largely inspired by the design of the Cognitive Bias Codex, originally developed by John Manoogian III (jm3) and based on the conceptual organization of biases by Buster Benson, as seen here: ', None),
            ('Cognitive Bias Codex on Wikimedia Commons', 'https://commons.wikimedia.org/wiki/File:Cognitive_bias_codex_en.svg'),
            ('.', None),
        ],
        [
            ('2. Unlike cognitive biases, which thanks to Buster Benson have a relatively structured and consolidated presence on Wikipedia, this categorization of biases in human-AI interaction is an exploratory effort by ', None),
            ('Zezhen Wu', 'https://www.linkedin.com/in/zezhenwu/'),
            (',', None),
            (' it extends beyond strictly defined "biases" to organize four broader domains where both AI and human cognitive biases may shape interactions,', None),
        ],
        [
            ('drawing on an attempt-to-be-exhaustive synthesis of academic literature and Wikipedia-based scraping assisted by Codex, and is shared as an open, non-canonical resource that the public is invited to fork and refine via ', None),
            ('GitHub', 'https://github.com/littlehifive/ai-bias-codex'),
            ('.', None),
        ],
    ]
    for line in rendered_lines:
        footer.append(
            f'<text x="{FOOTER_LEFT_X}" y="{y}" fill="{FOOTER_TEXT_COLOR}" font-size="{FOOTER_FONT_SIZE:.1f}px">'
        )
        for text, href in line:
            if href:
                footer.append(
                    f'<a xlink:href="{href}"><tspan text-decoration="underline">{escape(text)}</tspan></a>'
                )
            else:
                footer.append(f'<tspan>{escape(text)}</tspan>')
        footer.append("</text>")
        y += FOOTER_LINE_HEIGHT
    footer.append("</g>")
    return "\n".join(footer)


def append_footer_notes(svg_text):
    if "</svg>" not in svg_text:
        raise ValueError("Unable to append footer notes; SVG closing tag not found.")
    return svg_text.replace("</svg>", footer_notes_svg() + "\n\n</svg>")


def expand_canvas_height(svg_text):
    updated = re.sub(r'height="1500"', f'height="{EXPANDED_CANVAS_HEIGHT}"', svg_text, count=1)
    updated = re.sub(r'viewBox="0 0 1900 1500"', f'viewBox="0 0 1900 {EXPANDED_CANVAS_HEIGHT}"', updated, count=1)
    return updated


def main():
    parser = argparse.ArgumentParser(description="Fill the original cognitive bias codex SVG template with AI-bias content.")
    parser.add_argument("dataset", type=Path, help="Curated AI bias dataset JSON.")
    parser.add_argument("template", type=Path, help="Original SVG template path.")
    parser.add_argument("output", type=Path, help="Output SVG path.")
    args = parser.parse_args()

    dataset = json.loads(args.dataset.read_text())
    svg = args.template.read_text()
    quadrant_colors = [quadrant["color"] for quadrant in dataset["quadrants"]]
    svg = apply_quadrant_colors(svg, quadrant_colors)

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

    final_svg = expand_canvas_height("".join(rebuilt))
    final_svg = apply_statement_text_colors(final_svg, quadrant_colors)
    final_svg = append_footer_notes(final_svg)

    args.output.write_text(final_svg)
    print(f"Wrote {args.output}")
    print(f"Visible leaves: {visible_leaves}")
    if omitted:
        print("Omitted due to template slot limits:")
        for name in omitted:
            print(f"- {name}")


if __name__ == "__main__":
    main()
