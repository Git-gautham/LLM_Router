# PRISM: Privacy-Aware LLM Router

PRISM is an intelligent routing layer for LLM requests. It decides whether a prompt should be processed locally, sent to a cloud model simulation, or blocked based on risk. The project combines a React/Vite interface, FastAPI backend, trained sensitivity classifier, deterministic security detectors, risk engine, and policy engine to minimize sensitive-data leakage.

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
- React/Vite chat interface with named chat history
- Image, webcam, and document attachments
- PDF/image OCR and TXT, DOCX, and XLSX extraction
- Combined scanning of the user question and attached file
- Risk and routing metadata shown for every assistant response
- Explicit user confirmation before any cloud request
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
├── backend/
│   └── main.py                # FastAPI API
├── frontend/
│   ├── src/                   # React UI
│   └── package.json
├── classifier.py              # Baseline text classifier
├── main.py                    # Interactive router entrypoint
├── router.py                  # Request routing orchestration
├── start-prism.ps1            # Start backend and frontend on Windows
├── stop-prism.ps1             # Stop PRISM processes on Windows
├── requirements.txt
├── .gitignore
└── README.md
```

## How it works

The router follows this flow for both text and file requests:

1. Accepts a user question and optional document or image
2. Extracts and normalizes text from the attachment if needed
3. Combines the user question and extracted content
4. Runs deterministic detectors for PII, secrets, and code over the combined input
5. Classifies the text using the trained DistilBERT model
6. Calculates a risk score from the sensitivity label and detected indicators
7. Applies a policy decision:
   - `BLOCK`: do not process the request
   - `LOCAL`: keep processing on-device
   - `CLOUD`: route to a cloud LLM when safe
8. Returns the final result and response handling

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

## Running the command-line app

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

## Running the PRISM web app

The web app consists of:

- FastAPI backend at `http://127.0.0.1:8000`
- React/Vite frontend at `http://127.0.0.1:5173`

### Windows quick start

From the project root, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-prism.ps1
```

The script opens separate backend and frontend terminals, waits for both services to respond, and opens the browser automatically.

To stop the services and their launcher terminals:

```powershell
.\stop-prism.ps1
```

### Manual start

Install frontend dependencies:

```powershell
cd frontend
npm install
```

Start the backend from the project root:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, start the frontend:

```powershell
cd frontend
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173`. Backend API documentation is available at `http://127.0.0.1:8000/docs`.

### Supported attachments

The web app accepts:

- PDF, TXT, DOCX, and XLSX documents
- PNG and JPG/JPEG images
- Webcam photos

Images and scanned PDFs use OCR when needed. The question and extracted attachment text are scanned together, so sensitive information typed in the question cannot bypass PII or secret detection.

### Optional cloud routing

Public, low-risk prompts may be classified as `CLOUD`. PRISM never sends them
to a cloud provider automatically. The response first shows a **Proceed to
cloud** button. Only after the user selects it does the backend make a cloud
request.

The initial adapter uses OpenRouter's OpenAI-compatible API. Configure it in
the backend terminal before starting PRISM:

```powershell
$env:OPENROUTER_API_KEY = "your-key"
$env:OPENROUTER_MODEL = "liquid/lfm-2.5-2.6b:free"
$env:OPENROUTER_FALLBACK_MODELS = "google/gemma-4-26b-a4b-it:free,nvidia/nemotron-3.5-lightning:free"
.\start-prism.ps1
```

Do not commit the API key. The model name can be changed without a code
change. Free availability and rate limits vary by provider and can change, so
verify the current limits before relying on a free tier.

Other providers worth considering are Google's Gemini API free tier, Groq's
developer free tier, and Hugging Face Inference Providers. Each requires its
own API key, quotas, and adapter; OpenRouter is the provider currently wired
into PRISM.

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
