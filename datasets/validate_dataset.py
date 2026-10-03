import csv
from collections import Counter
from pathlib import Path


DATASET = Path("datasets/sensitivity_dataset.csv")

EXPECTED_LABELS = {
    "Public",
    "Internal",
    "Confidential",
    "Secret",
}


def validate_dataset():
    if not DATASET.exists():
        print(f"ERROR: Dataset not found: {DATASET}")
        return

    rows = []

    with open(DATASET, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required_columns = {"text", "label"}

        if not required_columns.issubset(reader.fieldnames):
            print("ERROR: Dataset must contain 'text' and 'label' columns.")
            return

        for row in reader:
            rows.append(row)

    labels = [row["label"] for row in rows]
    texts = [row["text"] for row in rows]

    label_counts = Counter(labels)

    print("Dataset Validation")
    print("=" * 50)

    print(f"Total examples: {len(rows)}")

    print("\nClass distribution:")
    for label in sorted(EXPECTED_LABELS):
        print(f"{label}: {label_counts[label]}")

    print("\nMissing labels:")
    missing_labels = EXPECTED_LABELS - set(labels)

    if missing_labels:
        print(missing_labels)
    else:
        print("None")

    print("\nEmpty texts:")
    empty_texts = sum(
        1 for text in texts
        if not text.strip()
    )
    print(empty_texts)

    print("\nDuplicate texts:")
    duplicate_count = len(texts) - len(set(texts))
    print(duplicate_count)

    print("\nUnexpected labels:")
    unexpected = set(labels) - EXPECTED_LABELS

    if unexpected:
        print(unexpected)
    else:
        print("None")

    print("\nValidation complete.")


if __name__ == "__main__":
    validate_dataset()