"""
Suggest sensitivity labels for review_queue.csv with a local Ollama model,
then write a small random sample for you to spot-check by hand.

Usage (from the project root, with Ollama running):
    python datasets/label_with_qwen.py --limit 500
    python datasets/label_with_qwen.py --limit 0        # whole queue (overnight)

Outputs (in datasets/processed/):
    review_queue_qwen.csv   every processed row + qwen_label / qwen_reason
    spot_check.csv          random sample; fill the human_label column

Safety rule: a row with PII (flagged by PII Shield or by our own detector)
can never be labelled Public, and a row where our secret detector fires
is always Secret. qwen's original answer is kept in qwen_label_raw.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import ollama
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from detectors.pii_detector import detect_pii
from detectors.secret_detector import detect_secrets

PROCESSED = ROOT / "datasets" / "processed"
QUEUE = PROCESSED / "review_queue.csv"
OUTPUT = PROCESSED / "review_queue_qwen.csv"
SPOT_CHECK = PROCESSED / "spot_check.csv"

LABELS = ["Public", "Internal", "Confidential", "Secret"]

# Save progress this often so a crash or reboot overnight loses little.
SAVE_EVERY = 50

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
The "label" value must be one word: Public, Internal, Confidential or Secret.
Answer only with JSON: {"label": "<one word>", "reason": "<max 15 words>"}"""


def parse_label(value: str) -> str | None:
    """
    Accept "Confidential", "confidential." or a copied definition such as
    "Public: general knowledge ..." by reading the first label word.
    """
    match = re.match(r"\s*(public|internal|confidential|secret)\b", value, re.IGNORECASE)
    return match.group(1).capitalize() if match else None


def suggest_label(model: str, text: str) -> tuple[str, str]:
    # One retry: small models occasionally return broken JSON.
    for _ in range(2):
        try:
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
            data = json.loads(response["message"]["content"])
        except Exception:
            continue

        label = parse_label(str(data.get("label", "")))
        if label:
            return label, str(data.get("reason", "")).strip()

    return "ERROR", "Model did not return a valid label"


def source_has_pii(row: pd.Series) -> bool:
    """PII Shield rows enter the queue as Confidential only when has_pii was true."""
    return row.get("source") == "pii_shield" and row.get("label") == "Confidential"


def apply_safety_rule(row: pd.Series) -> pd.Series:
    raw = row["qwen_label_raw"]
    text = str(row["text"])
    label, note = raw, ""

    if raw != "ERROR":
        if detect_secrets(text)["has_secret"]:
            label, note = "Secret", "secret detector fired"
        elif raw == "Public" and (source_has_pii(row) or detect_pii(text)["has_pii"]):
            label, note = "Confidential", "PII present, Public not allowed"

    row["qwen_label"] = label
    row["label_adjusted"] = note
    return row


def save(result: pd.DataFrame) -> None:
    result.to_csv(OUTPUT, index=False, encoding="utf-8-sig")


def display_text(value: object, limit: int = 70) -> str:
    """Keep progress logging safe on Windows consoles with legacy encodings."""
    preview = str(value).replace("\r", " ").replace("\n", " ")[:limit]
    return preview.encode("ascii", errors="replace").decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--limit", type=int, default=500, help="0 = whole queue")
    parser.add_argument("--sample", type=int, default=100)
    args = parser.parse_args()

    queue = pd.read_csv(QUEUE, encoding="utf-8-sig")

    # Resume: skip rows labelled in an earlier run, but retry ERROR rows.
    if OUTPUT.exists():
        done = pd.read_csv(OUTPUT, encoding="utf-8-sig")
        if "qwen_label_raw" not in done.columns:
            # File from the first version of this script.
            done["qwen_label_raw"] = done["qwen_label"]
        done = done[done["qwen_label_raw"] != "ERROR"]
        queue = queue[~queue["text_hash"].isin(done["text_hash"])]
    else:
        done = pd.DataFrame()

    batch = queue if args.limit == 0 else queue.head(args.limit)
    print(f"Rows to label: {len(batch):,} (already done: {len(done):,})")

    new_rows = []
    for number, (_, row) in enumerate(batch.iterrows(), start=1):
        label, reason = suggest_label(args.model, str(row["text"]))
        row = row.copy()
        row["qwen_label_raw"] = label
        row["qwen_reason"] = reason
        row["qwen_model"] = args.model
        new_rows.append(row)
        print(f"[{number}/{len(batch)}] {label:12} {display_text(row['text'])}")

        if number % SAVE_EVERY == 0:
            save(pd.concat([done, pd.DataFrame(new_rows)], ignore_index=True))

    result = pd.concat([done, pd.DataFrame(new_rows)], ignore_index=True)

    # Re-applied to every row, including ones from earlier runs.
    result = result.apply(apply_safety_rule, axis=1)
    save(result)

    print("\nFinal labels by source:")
    print(pd.crosstab(result["source"], result["qwen_label"]))
    print(f"\nChanged by the safety rule: {(result['label_adjusted'] != '').sum():,}")

    # Random sample for a human to check. Keep qwen's answer hidden while
    # you label if you want an unbiased check.
    sample = result[result["qwen_label"] != "ERROR"].sample(
        n=min(args.sample, len(result)), random_state=42
    )
    sample = sample[["text_hash", "source", "text", "qwen_label", "qwen_reason"]].copy()
    sample["human_label"] = ""

    # Do not wipe a spot-check someone has already started filling in.
    if SPOT_CHECK.exists():
        existing = pd.read_csv(SPOT_CHECK, encoding="utf-8-sig")
        if existing["human_label"].notna().any():
            print(f"\n{SPOT_CHECK} already has human labels; left unchanged.")
            return

    sample.to_csv(SPOT_CHECK, index=False, encoding="utf-8-sig")

    print(f"\nWrote {OUTPUT}")
    print(f"Fill the human_label column in {SPOT_CHECK} and compare.")


if __name__ == "__main__":
    main()
