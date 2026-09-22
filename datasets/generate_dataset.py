import csv
import random
from pathlib import Path


OUTPUT_FILE = Path("datasets/sensitivity_dataset.csv")

examples = {
    "Public": [
        "Explain machine learning in simple terms.",
        "What is the difference between RAM and ROM?",
        "Explain how a neural network works.",
        "What is a transformer model?",
        "Explain the basics of computer networks.",
        "What is supervised learning?",
        "Explain the concept of cloud computing.",
        "How does an operating system work?",
        "What is the purpose of a database?",
        "Explain the difference between AI and machine learning.",
        "What is a microcontroller?",
        "Explain how HTTP works.",
        "What is an API?",
        "Explain the concept of encryption.",
        "What is a convolutional neural network?",
    ],

    "Internal": [
        "Summarize our team's meeting agenda.",
        "Create a summary of the internal project discussion.",
        "Draft an agenda for our engineering team meeting.",
        "Organize the tasks discussed by our development team.",
        "Summarize the current progress of our internal software project.",
        "Prepare notes from our team's weekly meeting.",
        "Create a checklist for our internal testing process.",
        "Summarize the development team's planned activities.",
        "Draft an internal project status update.",
        "Organize these routine engineering tasks by priority.",
        "Prepare a summary of our team's sprint activities.",
        "Create a report about our internal development workflow.",
        "Summarize the team's software testing activities.",
        "Draft a message about the internal project schedule.",
        "Create a technical summary for our engineering team.",
    ],

    "Confidential": [
        "Summarize this employee salary report.",
        "Analyze the confidential employee performance report.",
        "Summarize the company's private financial projections.",
        "Review this confidential customer contract.",
        "Analyze the internal business acquisition proposal.",
        "Summarize the private sales forecast for next quarter.",
        "Review the confidential employee evaluation documents.",
        "Analyze this private customer information report.",
        "Summarize the company's confidential pricing strategy.",
        "Review the confidential legal agreement.",
        "Analyze this private business strategy document.",
        "Summarize the confidential HR investigation report.",
        "Review the company's private financial statement.",
        "Analyze the confidential supplier contract.",
        "Summarize this restricted business proposal.",
    ],

    "Secret": [
        "Here is the production password: SuperSecret123.",
        "Use this API key to access our production service: sk-example-123456789.",
        "The database password is AdminPassword987.",
        "Here is our AWS secret access key: example-secret-key.",
        "The production server login is admin with password P@ssword123.",
        "Store this private authentication token securely: token-example-12345.",
        "Our database connection string contains the password dbSecret456.",
        "Here is the private SSH key for the production server.",
        "The authentication secret for the application is secret-example-789.",
        "Use this access token for the production API: token-987654321.",
        "The administrator password for the server is RootPassword123.",
        "Here is the application's client secret: client-secret-example.",
        "The production database credentials are username admin and password Database123.",
        "This document contains our private encryption key.",
        "Here is the authentication token used by our backend service.",
    ],
}


def create_dataset():
    rows = []

    for label, sentences in examples.items():
        for sentence in sentences:
            rows.append({
                "text": sentence,
                "label": label
            })

    random.shuffle(rows)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset created: {OUTPUT_FILE}")
    print(f"Total examples: {len(rows)}")

    for label in examples:
        count = sum(1 for row in rows if row["label"] == label)
        print(f"{label}: {count}")


if __name__ == "__main__":
    create_dataset()