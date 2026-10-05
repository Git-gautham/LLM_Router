# Adaptive Hybrid LLM Router

An intelligent routing layer for LLM requests that decides whether a prompt should be processed locally, sent to a cloud model, or blocked based on risk. The project combines a trained sensitivity classifier, deterministic security detectors, a risk engine, and a policy engine to minimize leakage of sensitive data.

## Why this project exists

Large language models are useful for many tasks, but sending confidential, internal, or personal information to external services can create privacy, compliance, and security risks. This router adds a safety control layer before any LLM request is sent.

It evaluates:

- text sensitivity (`Public`, `Internal`, `Confidential`, `Secret`)
- personally identifiable information (PII)
- credential and secret patterns
- code snippets and structured data indicators
- risk score and routing policy

## Features

- DistilBERT-based sensitivity classifier for prompt classification
- PII detection for emails, phone numbers, SSNs, and similar patterns
- Secret detection for API keys, tokens, and credentials
- Code detection to flag code-heavy inputs
- Risk scoring to rank the danger level of a request
- Policy-driven routing decisions:
  - `BLOCK` for secrets or high-risk content
  - `LOCAL` for confidential/internal or PII-heavy content
  - `CLOUD` for clearly public requests
- Interactive command-line interface for text and document analysis
- Local LLM integration through Ollama

## Project structure

```text
LLM_Router/
├── app/
│   └── local_llm.py            # Local Ollama integration
├── datasets/
│   └── sensitivity_dataset.csv
├── detectors/
│   ├── code_detector.py
│   ├── pii_detector.py
│   └── secret_detector.py
├── ml/
│   ├── predict.py              # DistilBERT inference
│   └── train_distilbert.py    # Model training pipeline
├── models/
│   └── distilbert_router/     # Trained checkpoints
├── policy/
│   └── policy_engine.py       # Routing policy
├── preprocessing/
│   ├── document_processor.py
│   ├── feature_generator.py
│   ├── metadata_extractor.py
│   └── pipeline.py
├── risk/
│   └── risk_engine.py         # Risk scoring logic
├── classifier.py              # Baseline text classifier
├── main.py                    # Interactive router entrypoint
├── router.py                  # Request routing orchestration
├── requirements.txt
├── .gitignore
└── README.md
```

## How it works

The router follows this flow:

1. Accepts user input and optional document file
2. Extracts and normalizes text from the document if needed
3. Runs deterministic detectors for PII, secrets, and code
4. Classifies the text using the trained DistilBERT model
5. Calculates a risk score from the sensitivity label and detected indicators
6. Applies a policy decision:
   - `BLOCK`: do not process the request
   - `LOCAL`: keep processing on-device
   - `CLOUD`: route to a cloud LLM when safe
7. Returns the final result and response handling

## Setup

### Prerequisites

- Python 3.10+
- pip
- Ollama installed and running locally

### 1) Create and activate a virtual environment

Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Pull the local model used by the app

```bash
ollama pull qwen2.5:3b
```

The local LLM gateway uses the `qwen2.5:3b` model by default via Ollama.

## Running the app

From the project root:

```bash
python main.py
```

You will be prompted to enter:

- a question
- an optional document path

Example:

```text
Question: Summarize our employee handbook
Document path: C:\path\to\employee_handbook.pdf
```

The router will classify the content, calculate the risk, apply policy logic, and return a routing decision.

## Training the model

The repository includes a DistilBERT training flow in `ml/train_distilbert.py`.

```bash
python ml/train_distilbert.py
```

This script:

- loads `datasets/sensitivity_dataset.csv`
- splits data into train/test sets
- fine-tunes a DistilBERT classifier on the sensitivity labels
- saves checkpoints to `models/distilbert_router/`

## Current status

This project is a working prototype for privacy-aware LLM routing. It includes:

- local document/text analysis
- risk-aware classification and routing policy
- local model inference
- local LLM integration

The cloud route is currently simulated in the code and is intended as a placeholder for future provider integrations.

## Example policy behavior

- `Public` text with no sensitive markers -> `CLOUD`
- `Internal` or `Confidential` content -> `LOCAL`
- PII detected -> `LOCAL`
- Secret or credential pattern detected -> `BLOCK`

## Notes

- The model is designed to detect sensitivity level, not to guarantee general-purpose redaction.
- The policy layer is intentionally conservative and favors local processing when uncertainty exists.
- For production use, consider adding stronger validation, logging, audit trails, and cloud provider integration.

## License

This project does not currently declare a license file. If you intend to distribute or reuse it publicly, add a suitable open-source license before sharing outside your immediate team.
