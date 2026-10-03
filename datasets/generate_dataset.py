import csv
import random
from pathlib import Path


OUTPUT_FILE = Path("datasets/sensitivity_dataset.csv")


DATA = {
    "Public": [
        "What is machine learning?",
        "Explain how a neural network works.",
        "What is the difference between Python and Java?",
        "Explain the concept of cloud computing.",
        "What is an operating system?",
        "How does HTTPS work?",
        "Explain supervised learning.",
        "What is a database?",
        "What is an API?",
        "Explain the concept of artificial intelligence.",
        "What is a convolutional neural network?",
        "Explain what an IP address is.",
        "What is version control?",
        "How does Git work?",
        "Explain the difference between RAM and storage.",
        "What is Docker?",
        "What is Kubernetes?",
        "Explain REST APIs.",
        "What is an algorithm?",
        "What is natural language processing?",
    ],

    "Internal": [
        "Summarize our software development workflow.",
        "Explain the internal process for submitting a project update.",
        "Prepare a summary of our team's weekly engineering meeting.",
        "Describe the internal procedure for requesting technical support.",
        "Summarize the development team's current testing workflow.",
        "Explain our organization's software deployment process.",
        "Create notes for an internal engineering discussion.",
        "Summarize the project milestones for our development team.",
        "Explain the internal process for reviewing code changes.",
        "Prepare an internal technical status report.",
        "Summarize our team's project management workflow.",
        "Explain the internal procedure for reporting a software issue.",
        "Create an internal checklist for software testing.",
        "Summarize the team's development responsibilities.",
        "Prepare an internal document describing our release process.",
        "Explain how our engineering team coordinates development tasks.",
        "Summarize an internal architecture discussion.",
        "Create an internal project progress summary.",
        "Explain our team's documentation process.",
        "Prepare internal notes about the software development schedule.",
    ],

    "Confidential": [
        "Summarize this employee performance review.",
        "Analyze the employee's salary information.",
        "Review this customer's personal information.",
        "Summarize this patient's medical report.",
        "Analyze this company's confidential financial report.",
        "Review this employee's disciplinary record.",
        "Summarize the confidential legal agreement.",
        "Analyze the customer's private transaction history.",
        "Review this patient's laboratory results.",
        "Summarize the company's confidential business strategy.",
        "Analyze this employee compensation document.",
        "Review this confidential client contract.",
        "Summarize the company's private financial projections.",
        "Analyze this customer's private account information.",
        "Review this confidential human resources document.",
        "Summarize this patient's clinical history.",
        "Analyze this private employee assessment.",
        "Review the confidential acquisition proposal.",
        "Summarize this company's internal financial statements.",
        "Analyze this confidential legal case document.",
    ],

    "Secret": [
        "Use this API_KEY=FAKE_API_KEY_123456789 to access the service.",
        "The database password is FakePassword123.",
        "Here is the access_token=FAKE_TOKEN_987654321.",
        "Use this private key to authenticate the server.",
        "The production database credentials are included below.",
        "Here is the service API key for authentication.",
        "The administrator password is provided in this message.",
        "Use the following access token to call the API.",
        "The SSH private key is included in this document.",
        "Here are the production credentials for the database.",
        "The authentication token for the application is included here.",
        "This message contains a secret API credential.",
        "The database connection string contains authentication credentials.",
        "Here is the private key required for server access.",
        "The cloud service access key is included below.",
        "This configuration contains the production password.",
        "The deployment token is included in the configuration.",
        "These are the credentials required to access the server.",
        "The application secret key is included here.",
        "This document contains authentication credentials.",
    ],
}


def generate_dataset():
    rows = []

    for label, examples in DATA.items():
        for text in examples:
            rows.append({
                "text": text,
                "label": label,
            })

    random.seed(42)
    random.shuffle(rows)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["text", "label"],
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset created: {OUTPUT_FILE}")
    print(f"Total examples: {len(rows)}")

    for label in DATA:
        print(f"{label}: {len(DATA[label])}")


if __name__ == "__main__":
    generate_dataset()