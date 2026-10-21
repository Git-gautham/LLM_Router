
from pathlib import Path
import sys
import time

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add the project root so existing modules can be imported.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ml.predict import SensitivityClassifier
from app.local_llm import ask_local_llm

app = FastAPI(title="PRISM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = None


class InferenceRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PRISM API"}


@app.post("/api/infer")
def infer(request: InferenceRequest):
    global classifier

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Enter a message.")

    start = time.perf_counter()

    try:
        if classifier is None:
            classifier = SensitivityClassifier(
                model_path=str(
                    PROJECT_ROOT / "models" / "distilbert_router" / "checkpoint-24"
                )
            )

        sensitivity = classifier.predict(question)

        # Initial integration: answer locally using the existing Ollama function.
        # We will connect the project's full AdaptiveRouter logic after verifying
        # its existing interface.
        answer = ask_local_llm(
            "Answer the user's request helpfully. Keep the response clear.\n\n"
            f"User message:\n{question}"
        )

        latency_ms = round((time.perf_counter() - start) * 1000)

        return {
            "answer": answer,
            "sensitivity": sensitivity["label"],
            "confidence": sensitivity["confidence"],
            "selected_model": "qwen2.5:3b",
            "route": "local",
            "cloud_used": False,
            "latency_ms": latency_ms,
            "explanation": (
                "Sensitivity was classified using the existing DistilBERT model. "
                "This initial API sends the prompt to the local Ollama model."
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "PRISM could not process this message. Check that the model files "
                "exist and Ollama is running. Error: " + str(exc)
            ),
        ) from exc
