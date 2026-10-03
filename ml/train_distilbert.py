import numpy as np
import pandas as pd

from datasets import Dataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
)

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)


DATASET_PATH = "datasets/sensitivity_dataset.csv"
MODEL_NAME = "distilbert-base-uncased"

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


def load_data():
    df = pd.read_csv(DATASET_PATH)

    df["label_id"] = df["label"].map(LABEL2ID)

    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["label"],
    )

    train_dataset = Dataset.from_pandas(
        train_df[["text", "label_id"]],
        preserve_index=False,
    )

    test_dataset = Dataset.from_pandas(
        test_df[["text", "label_id"]],
        preserve_index=False,
    )

    train_dataset = train_dataset.rename_column(
        "label_id",
        "labels",
    )

    test_dataset = test_dataset.rename_column(
        "label_id",
        "labels",
    )

    return train_dataset, test_dataset


def compute_metrics(eval_prediction):
    predictions, labels = eval_prediction

    predictions = np.argmax(
        predictions,
        axis=1,
    )

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="weighted",
        zero_division=0,
    )

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def main():

    print("Loading dataset...")

    train_dataset, test_dataset = load_data()

    print(f"Training examples: {len(train_dataset)}")
    print(f"Testing examples: {len(test_dataset)}")

    print("\nLoading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            padding="max_length",
            truncation=True,
            max_length=128,
        )

    train_dataset = train_dataset.map(
        tokenize,
        batched=True,
    )

    test_dataset = test_dataset.map(
        tokenize,
        batched=True,
    )

    print("\nLoading DistilBERT model...")

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=len(LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )

    training_args = TrainingArguments(
        output_dir="./models/distilbert_router",
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        report_to="none",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        compute_metrics=compute_metrics,
    )

    print("\nStarting training...")

    trainer.train()

    print("\nFinal evaluation:")

    results = trainer.evaluate()

    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

    print("\nClassification report:")

    predictions = trainer.predict(test_dataset)

    predicted_labels = np.argmax(
        predictions.predictions,
        axis=1,
    )

    print(
        classification_report(
            predictions.label_ids,
            predicted_labels,
            target_names=LABELS,
            zero_division=0,
        )
    )

    print("\nTraining complete.")


if __name__ == "__main__":
    main()