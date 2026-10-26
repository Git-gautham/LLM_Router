"""Build classifier splits using accepted labels and Qwen-reviewed rows."""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "datasets" / "processed"
ALL_DATASET = PROCESSED / "sensitivity_dataset_all.csv"
QWEN_DATASET = PROCESSED / "review_queue_qwen.csv"
LABELS = ["Public", "Internal", "Confidential", "Secret"]
SEED = 42


def load_inputs() -> pd.DataFrame:
    accepted = pd.read_csv(ALL_DATASET, encoding="utf-8-sig")
    accepted = accepted[accepted["review_required"] == False].copy()

    qwen = pd.read_csv(QWEN_DATASET, encoding="utf-8-sig")
    qwen = qwen[qwen["qwen_label"].isin(LABELS)].copy()
    qwen = qwen.rename(columns={"qwen_label": "label"})

    combined = pd.concat([accepted, qwen], ignore_index=True, sort=False)
    combined["text"] = combined["text"].fillna("").astype(str).str.strip()
    combined["label"] = combined["label"].astype(str).str.strip()
    combined = combined[combined["label"].isin(LABELS)]
    combined = combined[combined["text"].str.len() > 0]
    combined = combined.drop_duplicates(subset=["text_hash"], keep="last")

    if combined.empty:
        raise ValueError("No usable labeled rows were found.")

    return combined[["text", "label"]].reset_index(drop=True)


def write_split(frame: pd.DataFrame, name: str) -> None:
    path = PROCESSED / f"sensitivity_dataset_{name}.csv"
    frame.to_csv(path, index=False, encoding="utf-8")
    print(f"{name}: {len(frame):,} rows -> {path}")


def main() -> None:
    dataset = load_inputs()
    print("Combined label counts:")
    print(dataset["label"].value_counts().reindex(LABELS, fill_value=0))

    train, remainder = train_test_split(
        dataset,
        test_size=0.2,
        random_state=SEED,
        stratify=dataset["label"],
    )
    validation, test = train_test_split(
        remainder,
        test_size=0.5,
        random_state=SEED,
        stratify=remainder["label"],
    )

    write_split(train, "train")
    write_split(validation, "val")
    write_split(test, "test")


if __name__ == "__main__":
    main()
