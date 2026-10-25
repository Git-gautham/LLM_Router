"""
Suggest sensitivity labels for review_queue.csv with a local Ollama model,
then write a small random sample for you to spot-check by hand.

Usage (from the project root, with Ollama running):
    python datasets/label_with_qwen.py --limit 500
    python datasets/label_with_qwen.py --limit 500 --model qwen2.5:7b

Outputs (in datasets/processed/):
    review_queue_qwen.csv   every processed row + qwen_label / qwen_reason
    spot_check.csv          random sample; fill the human_label column
"""

import argparse
import json
from pathlib import Path

import ollama
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "datasets" / "processed"
QUEUE = PROCESSED / "review_queue.csv"
OUTPUT = PROCESSED / "review_queue_qwen.csv"
SPOT_CHECK = PROCESSED / "spot_check.csv"

LABELS = ["Public", "Internal", "Confidential", "Secret"]

SYSTEM_PROMPT = """You label text for a privacy router. Pick exactly one label:

Public: general knowledge or content anyone could see. No personal data,
  nothing tied to a specific company's private business.
Internal: routine work content of an organisation (meetings, schedules,
  process notes, team updates) that is not harmful if leaked.
Confidential: personal data about a real person (names with contact details,
  salary, health, ID numbers, addresses) or sensitive business data
  (finances, contracts, legal, deals, unreleased plans).
Secret: credentials or access material: passwords, API keys, tokens,
  private keys, connection strings with passwords.

If unsure between two labels, choose the MORE sensitive one.
Answer only with JSON: {"label": "<one label>", "reason": "<max 15 words>"}"""


def suggest_label(model: str, text: str) -> tuple[str, str]:
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            # Long emails confuse small models; the start is usually enough.
            {"role": "user", "content": text[:2000]},
        ],
        format="json",
        options={"temperature": 0},
    )

    try:
        data = json.loads(response["message"]["content"])
        label = str(data.get("label", "")).strip().capitalize()
        reason = str(data.get("reason", "")).strip()
    except (json.JSONDecodeError, AttributeError):
        return "ERROR", "Model did not return valid JSON"

    if label not in LABELS:
        return "ERROR", f"Unknown label: {label}"

    return label, reason


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--sample", type=int, default=100)
    args = parser.parse_args()

    queue = pd.read_csv(QUEUE, encoding="utf-8-sig")

    # Resume: skip rows labelled in an earlier run.
    if OUTPUT.exists():
        done = pd.read_csv(OUTPUT, encoding="utf-8-sig")
        queue = queue[~queue["text_hash"].isin(done["text_hash"])]
    else:
        done = pd.DataFrame()

    batch = queue.head(args.limit).copy()
    labels, reasons = [], []

    for number, text in enumerate(batch["text"], start=1):
        label, reason = suggest_label(args.model, str(text))
        labels.append(label)
        reasons.append(reason)
        print(f"[{number}/{len(batch)}] {label:12} {str(text)[:70]}")

    batch["qwen_label"] = labels
    batch["qwen_reason"] = reasons
    batch["qwen_model"] = args.model

    result = pd.concat([done, batch], ignore_index=True)
    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")

    print("\nSuggested labels by source:")
    print(pd.crosstab(result["source"], result["qwen_label"]))

    # Random sample for a human to check. Do not show qwen's answer
    # first if you want an unbiased check; it is kept in its own column.
    sample = result[result["qwen_label"] != "ERROR"].sample(
        n=min(args.sample, len(result)), random_state=42
    )
    sample = sample[["text_hash", "source", "text", "qwen_label", "qwen_reason"]].copy()
    sample["human_label"] = ""
    sample.to_csv(SPOT_CHECK, index=False, encoding="utf-8-sig")

    print(f"\nWrote {OUTPUT}")
    print(f"Fill the human_label column in {SPOT_CHECK} and compare.")


if __name__ == "__main__":
    main()
