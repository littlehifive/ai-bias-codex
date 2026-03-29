#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path


DATASET_TITLE = "The AI Bias Codex"
DATASET_SUBTITLE = "A Wikipedia-backed map of human judgment distortions in human-AI interaction."

QUADRANT_SPECS = {
    "Trust and Reliance Miscalibration": {
        "id": "trust-reliance-miscalibration",
        "title": "We trust AI too much or too little",
        "research_title": "Trust and Reliance Miscalibration",
        "failure_point": "whether we follow AI appropriately",
        "color": "#1f6fa8",
        "statement_labels": {
            "Over-reliance and deference": "We over-defer to automated answers and system authority",
            "Credibility shortcuts": "Surface polish and credibility cues make AI feel trustworthy",
            "Monitoring collapse": "Once AI feels reliable, we monitor it less closely",
            "Resistance and backlash": "We resist AI when it feels controlling or threatens judgment",
        },
        "support_label": "Trust depends on calibration, oversight, and perceived control",
    },
    "Belief Reinforcement and Selective Uptake": {
        "id": "belief-reinforcement-selective-uptake",
        "title": "We use AI to confirm what we already believe",
        "research_title": "Belief Reinforcement and Selective Uptake",
        "failure_point": "how our prior beliefs shape what we take from AI",
        "color": "#7c7c7c",
        "statement_labels": {
            "Confirmation-preserving interpretation": "We interpret AI output in ways that protect prior beliefs",
            "Selective intake and avoidance": "We seek agreeable answers and overlook disconfirming parts",
            "Belief persistence and evidence filtering": "We preserve beliefs by filtering evidence and examples",
            "Reinforcement loops": "Recommendation loops keep feeding what already fits",
        },
        "support_label": "Repeated phrasing blurs memory, source, and certainty",
    },
    "Judgment Steering by Anchors and Frames": {
        "id": "judgment-steering-anchors-frames",
        "title": "AI's suggestions steer our choices",
        "research_title": "Judgment Steering by Anchors and Frames",
        "failure_point": "how AI presentation shapes our choices",
        "color": "#0a8f83",
        "statement_labels": {
            "Reference-point effects": "Initial suggestions and wording shift downstream judgment",
            "Defaults and comparative choice steering": "Defaults and option sets quietly push us toward one choice",
            "Salience and retrieval effects": "What AI highlights feels most relevant and representative",
            "Prompting and designed influence": "Prompts and interface design cue decisions before reflection",
        },
        "support_label": "Repeated exposure and vivid examples amplify interface steering",
    },
    "Mind-Perception and Capability Illusions": {
        "id": "mind-perception-capability-illusions",
        "title": "We mistake AI for understanding more than it does",
        "research_title": "Mind-Perception and Capability Illusions",
        "failure_point": "how we misunderstand what the AI is",
        "color": "#5d8b1a",
        "statement_labels": {
            "Human-likeness attribution": "Human-like cues make AI seem more person-like than it is",
            "Social and agentic projection": "Conversation triggers social and empathic over-attribution",
            "Mind and intent attribution": "We read goals, beliefs, and intentions into system behavior",
            "Capability overestimation": "We overestimate how deeply the system actually understands",
        },
        "support_label": "Presence, patterns, and mental models fill in what AI lacks",
    },
}

DEFINITIONS = {
    "Algorithm aversion": "The tendency to distrust or reject algorithmic advice, especially after observing mistakes.",
    "Anchoring effect": "Judgments are pulled toward an initial reference point or suggestion.",
    "Anthropomorphism": "The attribution of human traits, motives, or feelings to non-human entities.",
    "Attentional bias": "The tendency to notice some cues more readily than competing cues.",
    "Authority bias": "The tendency to give extra weight to opinions or outputs associated with authority.",
    "Automation bias": "The tendency to favor automated suggestions and ignore contradictory non-automated information.",
    "Availability cascade": "A belief gains plausibility and spread through repetition and social reinforcement.",
    "Availability heuristic": "People judge importance or likelihood by how easily examples come to mind.",
    "Belief perseverance": "A belief can persist even after strong contrary evidence appears.",
    "Bias blind spot": "People are quicker to detect bias in others than in themselves.",
    "Cherry picking": "Only the evidence that supports a preferred conclusion is selected while conflicting evidence is ignored.",
    "Choice architecture": "The design of how options are presented can shape later decisions.",
    "Computers are social actors": "People often apply human social rules and expectations to computers and software agents.",
    "Confirmation bias": "People search for, interpret, and recall information in ways that support what they already believe.",
    "Credibility": "Credibility is the perceived believability or trustworthiness of a source or message.",
    "Decoy effect": "Adding an asymmetrically inferior option can shift preferences between the original options.",
    "Default effect": "People disproportionately stick with preselected or default options.",
    "Echo chamber (media)": "Beliefs are amplified when repeated inside a closed, like-minded information environment.",
    "ELIZA effect": "People can attribute understanding or empathy to a conversational program beyond what it warrants.",
    "False consensus effect": "People overestimate how widely their own beliefs and choices are shared by others.",
    "Filter bubble": "Personalized curation can isolate users inside a narrower information environment.",
    "Fluency heuristic": "Information that feels easier to process is often judged as more credible or preferable.",
    "Framing effect (psychology)": "Decisions can change when equivalent options are presented in different ways.",
    "Halo effect": "One positive surface trait can spill over and shape judgment of unrelated traits.",
    "Identifiable victim effect": "A vivid individual case can evoke stronger judgment than abstract statistics.",
    "Illusion of explanatory depth": "People often believe they understand a topic more deeply than they actually do.",
    "Illusory truth effect": "Repeated claims can feel truer even when repetition adds no evidence.",
    "Intentional stance": "Behavior is interpreted by ascribing beliefs, goals, and intentions to an entity.",
    "Learned helplessness": "Repeated experiences of lacking control can reduce initiative and independent action.",
    "Mental model": "An internal representation of how a system works.",
    "Mere-exposure effect": "Repeated exposure can increase familiarity and liking on its own.",
    "Mind projection fallacy": "A person mistakes subjective judgments or interpretations for objective properties of the world.",
    "Motivated reasoning": "Information is evaluated in ways that serve desired conclusions or identities.",
    "Nudge theory": "Behavior can be influenced by structuring the choice environment without removing options.",
    "Out-of-the-loop performance problem": "Performance can decline when automation removes people from active control and monitoring.",
    "Overconfidence effect": "Subjective confidence is often greater than objective accuracy.",
    "Pareidolia": "Meaningful patterns or agency are perceived in ambiguous stimuli where none may exist.",
    "Priming (psychology)": "Earlier stimuli can influence later judgments or responses without conscious intent.",
    "Processing fluency": "Easy-to-process information feels more familiar, trustworthy, or true.",
    "Reactance (psychology)": "A perceived threat to autonomy can trigger resistance to persuasion or control.",
    "Selective exposure theory": "People tend to choose information that reinforces their existing views.",
    "Selective perception": "People more readily notice and remember information that fits existing expectations.",
    "Situation awareness": "The perception and understanding of relevant elements in a changing environment.",
    "Social presence theory": "Digital interfaces can create a stronger sense that another social presence is really there.",
    "Source-monitoring error": "People can misremember where a piece of information originally came from.",
    "Trust (social science)": "Trust is the willingness to become vulnerable based on expectations about another actor's behavior.",
    "Vigilance": "Sustained attention is needed to detect infrequent signals over time.",
    "AI anthropomorphism": "Human-like feelings, intentions, or behavioral traits are attributed specifically to AI systems.",
}

SEED_PAGE_MAP = {
    "Algorithm aversion": "Algorithm aversion",
    "Anchoring effect": "Anchoring effect",
    "Anthropomorphism": "Anthropomorphism",
    "Attentional bias": "Choice architecture",
    "Authority bias": "Authority bias",
    "Automation bias": "Automation bias",
    "Availability cascade": "Echo chamber (media)",
    "Availability heuristic": "Choice architecture",
    "Belief perseverance": "Belief perseverance",
    "Bias blind spot": "Confirmation bias",
    "Cherry picking": "Confirmation bias",
    "Choice architecture": "Choice architecture",
    "Computers are social actors": "Computers are social actors",
    "Confirmation bias": "Confirmation bias",
    "Credibility": "Authority bias",
    "Decoy effect": "Decoy effect",
    "Default effect": "Default effect",
    "Echo chamber (media)": "Echo chamber (media)",
    "ELIZA effect": "ELIZA effect",
    "False consensus effect": "Computers are social actors",
    "Filter bubble": "Filter bubble",
    "Fluency heuristic": "Authority bias",
    "Framing effect (psychology)": "Framing effect (psychology)",
    "Halo effect": "Authority bias",
    "Identifiable victim effect": "Nudge theory",
    "Illusion of explanatory depth": "Illusion of explanatory depth",
    "Illusory truth effect": "Echo chamber (media)",
    "Intentional stance": "Intentional stance",
    "Learned helplessness": "Automation bias",
    "Mental model": "Intentional stance",
    "Mere-exposure effect": "Nudge theory",
    "Mind projection fallacy": "Intentional stance",
    "Motivated reasoning": "Motivated reasoning",
    "Nudge theory": "Nudge theory",
    "Out-of-the-loop performance problem": "Out-of-the-loop performance problem",
    "Overconfidence effect": "Illusion of explanatory depth",
    "Pareidolia": "Anthropomorphism",
    "Priming (psychology)": "Priming (psychology)",
    "Processing fluency": "Framing effect (psychology)",
    "Reactance (psychology)": "Algorithm aversion",
    "Selective exposure theory": "Selective exposure theory",
    "Selective perception": "Confirmation bias",
    "Situation awareness": "Out-of-the-loop performance problem",
    "Social presence theory": "Computers are social actors",
    "Source-monitoring error": "Belief perseverance",
    "Trust (social science)": "Authority bias",
    "Vigilance": "Out-of-the-loop performance problem",
    "AI anthropomorphism": "AI anthropomorphism",
}


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_leaf(quadrant_title, statement_label, page):
    title = page["wikipedia_page_title"]
    if title not in DEFINITIONS:
        raise KeyError(f"Missing one-sentence definition for {title}.")
    if title not in SEED_PAGE_MAP:
        raise KeyError(f"Missing seed-page mapping for {title}.")
    return {
        "quadrant": quadrant_title,
        "statement": statement_label,
        "bias_name": title,
        "one_sentence_definition": DEFINITIONS[title],
        "interaction_rationale": page["why_it_fits"],
        "wikipedia_url": page["wikipedia_url"],
        "link_kind": "exact",
        "seed_page": SEED_PAGE_MAP[title],
        "review_status": page["status"],
        "research_subcategory": page["subcategory"],
        "cross_links": page["cross_links"],
    }


def build_dataset(review):
    quadrants = []
    for category in review["recommended_codex_structure"]:
        spec = QUADRANT_SPECS[category["top_level_category"]]
        statements = []
        for subcategory in category["subcategories"]:
            label = spec["statement_labels"][subcategory["subcategory"]]
            statements.append(
                {
                    "id": slugify(subcategory["subcategory"]),
                    "label": label,
                    "research_subcategory": subcategory["subcategory"],
                    "leaves": [build_leaf(spec["title"], label, page) for page in subcategory["pages"]],
                }
            )

        support_label = spec["support_label"]
        statements.append(
            {
                "id": "support-context",
                "label": support_label,
                "research_subcategory": "support",
                "leaves": [build_leaf(spec["title"], support_label, page) for page in category["support_pages"]],
            }
        )

        quadrants.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "research_title": spec["research_title"],
                "failure_point": spec["failure_point"],
                "color": spec["color"],
                "statements": statements,
            }
        )

    return {
        "title": DATASET_TITLE,
        "subtitle": DATASET_SUBTITLE,
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
