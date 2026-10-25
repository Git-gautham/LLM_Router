
from pathlib import Path

import numpy as np
import pandas as pd
from datasets import Dataset
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)


# ============================================================
# CONFIGURATION
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT_DIR / "datasets" / "processed"

TRAIN_PATH = PROCESSED_DIR / "sensitivity_dataset_train.csv"
VAL_PATH = PROCESSED_DIR / "sensitivity_dataset_val.csv"
TEST_PATH = PROCESSED_DIR / "sensitivity_dataset_test.csv"

MODEL_NAME = "distilbert-base-uncased"

# Use a new directory to preserve your existing checkpoint.
OUTPUT_DIR = ROOT_DIR / "models" / "distilbert_router_v2"

LABELS = [
    "Public",
    "Internal",
    "Confidential",
    "Secret",
]

LABEL2ID = {
    label: index
    for index, label in enumerate(LABELS)
}

ID2LABEL = {
    index: label
    for label, index in LABEL2ID.items()
}

MAX_LENGTH = 128
TRAIN_BATCH_SIZE = 8
EVAL_BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 2e-5
SEED = 42


# ============================================================
# DATA LOADING AND VALIDATION
# ============================================================

def load_csv(path: Path) -> pd.DataFrame:
    """Load and validate a dataset CSV."""
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset file not found: {path}\n"
            "Run datasets/build_sensitivity_dataset.py first."
        )

    df = pd.read_csv(path)

    required_columns = {"text", "label"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"{path.name} is missing columns: {missing_columns}"
        )

    df = df[["text", "label"]].copy()

    df["text"] = df["text"].fillna("").astype(str).str.strip()
    df["label"] = df["label"].astype(str).str.strip()

    df = df[df["text"].str.len() > 0].copy()

    unknown_labels = sorted(set(df["label"]) - set(LABELS))

    if unknown_labels:
        raise ValueError(
            f"Unknown labels in {path.name}: {unknown_labels}"
        )

    df["label_id"] = df["label"].map(LABEL2ID)

    if df["label_id"].isna().any():
        raise ValueError(f"Some labels could not be mapped in {path.name}")

    df["label_id"] = df["label_id"].astype(int)

    if df.empty:
        raise ValueError(f"No usable rows found in {path}")

    print(f"\n{path.name}: {len(df):,} rows")
    print(df["label"].value_counts().reindex(LABELS, fill_value=0))

    return df


def check_split_leakage(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> None:
    """Check exact-text overlap between splits."""
    train_texts = set(train_df["text"].str.casefold())
    val_texts = set(val_df["text"].str.casefold())
    test_texts = set(test_df["text"].str.casefold())

    train_val = len(train_texts & val_texts)
    train_test = len(train_texts & test_texts)
    val_test = len(val_texts & test_texts)

    print("\nExact-text overlap:")
    print(f"Train–validation: {train_val}")
    print(f"Train–test:       {train_test}")
    print(f"Validation–test:  {val_test}")

    if train_val or train_test or val_test:
        raise ValueError(
            "Exact-text leakage detected between dataset splits. "
            "Fix the splits before training."
        )


def to_hf_dataset(df: pd.DataFrame) -> Dataset:
    """Convert a dataframe into the format expected by Trainer."""
    prepared = df[["text", "label_id"]].rename(
        columns={"label_id": "labels"}
    )

    return Dataset.from_pandas(
        prepared,
        preserve_index=False,
    )


# ============================================================
# METRICS
# ============================================================

def compute_metrics(eval_prediction):
    """Calculate metrics using the model's validation predictions."""
    logits = eval_prediction.predictions

    # Some models return a tuple of prediction arrays.
    if isinstance(logits, tuple):
        logits = logits[0]

    true_labels = eval_prediction.label_ids
    predicted_labels = np.argmax(logits, axis=-1)

    precision_macro, recall_macro, f1_macro, _ = (
        precision_recall_fscore_support(
            true_labels,
            predicted_labels,
            average="macro",
            zero_division=0,
        )
    )

    precision_weighted, recall_weighted, f1_weighted, _ = (
        precision_recall_fscore_support(
            true_labels,
            predicted_labels,
            average="weighted",
            zero_division=0,
        )
    )

    return {
        "accuracy": accuracy_score(true_labels, predicted_labels),
        "macro_precision": precision_macro,
        "macro_recall": recall_macro,
        "macro_f1": f1_macro,
        "weighted_precision": precision_weighted,
        "weighted_recall": recall_weighted,
        "weighted_f1": f1_weighted,
    }


def print_final_report(trainer: Trainer, test_dataset: Dataset) -> None:
    """Evaluate once on the held-out test set and print detailed metrics."""
    print("\n" + "=" * 60)
    print("FINAL TEST-SET EVALUATION")
    print("=" * 60)

    output = trainer.predict(test_dataset)
    logits = output.predictions

    if isinstance(logits, tuple):
        logits = logits[0]

    y_true = output.label_ids
    y_pred = np.argmax(logits, axis=-1)

    accuracy = accuracy_score(y_true, y_pred)

    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="macro",
        zero_division=0,
    )

    weighted_p, weighted_r, weighted_f1, _ = (
        precision_recall_fscore_support(
            y_true,
            y_pred,
            average="weighted",
            zero_division=0,
        )
    )

    print(f"Accuracy:          {accuracy:.4f}")
    print(f"Macro precision:   {macro_p:.4f}")
    print(f"Macro recall:      {macro_r:.4f}")
    print(f"Macro F1:          {macro_f1:.4f}")
    print(f"Weighted precision:{weighted_p:.4f}")
    print(f"Weighted recall:   {weighted_r:.4f}")
    print(f"Weighted F1:       {weighted_f1:.4f}")

    print("\nClassification report:")
    report = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(LABELS))),
        target_names=LABELS,
        digits=4,
        zero_division=0,
    )
    print(report)

    print("Confusion matrix (rows=true, columns=predicted):")
    matrix = confusion_matrix(
        y_true,
        y_pred,
        labels=list(range(len(LABELS))),
    )

    print(
        pd.DataFrame(
            matrix,
            index=[f"Actual_{label}" for label in LABELS],
            columns=[f"Pred_{label}" for label in LABELS],
        )
    )

    # Save detailed evaluation results.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report_dict = classification_report(
        y_true,
        y_pred,
        labels=list(range(len(LABELS))),
        target_names=LABELS,
        output_dict=True,
        zero_division=0,
    )

    pd.DataFrame(report_dict).transpose().to_csv(
        OUTPUT_DIR / "test_classification_report.csv",
        index=True,
    )

    pd.DataFrame(
        matrix,
        index=[f"Actual_{label}" for label in LABELS],
        columns=[f"Pred_{label}" for label in LABELS],
    ).to_csv(OUTPUT_DIR / "test_confusion_matrix.csv")

    print(f"\nEvaluation reports saved to: {OUTPUT_DIR}")


# ============================================================
# MAIN TRAINING FUNCTION
# ============================================================

def main():
    print("=" * 60)
    print("DISTILBERT PRIVACY SENSITIVITY CLASSIFIER")
    print("=" * 60)

    print(f"\nModel: {MODEL_NAME}")
    print(f"Output: {OUTPUT_DIR}")

    # 1. Load the pre-created, separate splits.
    print("\nLoading datasets...")

    train_df = load_csv(TRAIN_PATH)
    val_df = load_csv(VAL_PATH)
    test_df = load_csv(TEST_PATH)

    check_split_leakage(train_df, val_df, test_df)

    train_dataset = to_hf_dataset(train_df)
    val_dataset = to_hf_dataset(val_df)
    test_dataset = to_hf_dataset(test_df)

    print("\nDataset sizes:")
    print(f"Training:   {len(train_dataset):,}")
    print(f"Validation: {len(val_dataset):,}")
    print(f"Test:       {len(test_dataset):,}")

    # 2. Load tokenizer.
    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=MAX_LENGTH,
        )

    train_dataset = train_dataset.map(
        tokenize,
        batched=True,
        desc="Tokenizing training data",
    )

    val_dataset = val_dataset.map(
        tokenize,
        batched=True,
        desc="Tokenizing validation data",
    )

    test_dataset = test_dataset.map(
        tokenize,
        batched=True,
        desc="Tokenizing test data",
    )

    # 3. Load the base model with the project's four labels.
    print("\nLoading DistilBERT model...")

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    # 4. Configure training.
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="steps",
        logging_steps=100,
        learning_rate=LEARNING_RATE,
        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=EVAL_BATCH_SIZE,
        num_train_epochs=EPOCHS,
        weight_decay=0.01,
        seed=SEED,
        data_seed=SEED,
        load_best_model_at_end=True,
        metric_for_best_model="eval_macro_f1",
        greater_is_better=True,
        save_total_limit=2,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        processing_class=tokenizer,
        compute_metrics=compute_metrics,
    )

    # 5. Train using only training data. Validation selects the
    # best checkpoint; the test set is not used during training.
    print("\nStarting training...")
    trainer.train()

    # 6. Save the best model and tokenizer to the new directory.
    print("\nSaving best model...")

    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    print(f"Model saved to: {OUTPUT_DIR}")

    # 7. Evaluate on the held-out test split.
    print_final_report(trainer, test_dataset)

    print("\nTraining complete.")


if __name__ == "__main__":
    main()
