import csv

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score


DATASET = "datasets/sensitivity_dataset.csv"


def load_dataset():
    texts = []
    labels = []

    with open(DATASET, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            texts.append(row["text"])
            labels.append(row["label"])

    return texts, labels


def main():
    texts, labels = load_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels
    )

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2)
    )

    X_train_vectors = vectorizer.fit_transform(X_train)
    X_test_vectors = vectorizer.transform(X_test)

    model = LogisticRegression(
        max_iter=1000,
        random_state=42
    )

    model.fit(X_train_vectors, y_train)

    predictions = model.predict(X_test_vectors)

    accuracy = accuracy_score(y_test, predictions)

    print("\nBaseline Classifier Results")
    print("=" * 40)
    print(f"Accuracy: {accuracy:.4f}")

    print("\nClassification Report:")
    print(classification_report(y_test, predictions))


if __name__ == "__main__":
    main()