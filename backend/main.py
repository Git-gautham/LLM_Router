
from pathlib import Path
import sys
import time
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from router import AdaptiveRouter

app = FastAPI(title="PRISM API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = None


class InferenceRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Enter a message.")
        return value


def get_router():
    global router

    if router is None:
        model_path = (
            PROJECT_ROOT
            / "models"
            / "distilbert_router"
            / "checkpoint-24"
        )

        if not model_path.is_dir():
            raise RuntimeError(
                "Trained DistilBERT checkpoint was not found."
            )

        router = AdaptiveRouter(model_path=str(model_path))

    return router


def route_request(question: str, file_path: str | None = None) -> dict:
    start = time.perf_counter()
    result = get_router().route(text=question, file_path=file_path)
    return {
        "answer": result["response"],
        "sensitivity": result["sensitivity"],
        "confidence": result["confidence"],
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "risk_reasons": result["risk_reasons"],
        "policy_decision": result["decision"],
        "decision": result["decision"],
        "route": (
            "cloud_simulation"
            if result["decision"] == "CLOUD"
            else result["decision"].lower()
        ),
        "selected_model": (
            "cloud-simulation"
            if result["decision"] == "CLOUD"
            else "qwen2.5:3b"
            if result["decision"] == "LOCAL"
            else None
        ),
        "cloud_used": False,
        "latency_ms": round((time.perf_counter() - start) * 1000),
        "explanation": result["reason"],
        "reason": result["reason"],
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PRISM API"}


@app.post("/api/infer")
def infer(request: InferenceRequest):
    try:
        return route_request(request.question)

    except HTTPException:
        raise

    except Exception as exc:
        # Log details on the backend; don't expose internal errors
        # or file paths to the frontend.
        print(f"PRISM inference error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="PRISM could not process this message. "
                   "Check the backend logs and local model services.",
        ) from exc


@app.post("/api/infer-file")
async def infer_file(
    question: str = Form(...),
    file: UploadFile = File(...),
):
    suffix = Path(file.filename or "").suffix.lower()
    allowed_extensions = {".txt", ".pdf", ".docx", ".xlsx", ".png", ".jpg", ".jpeg"}
    if suffix not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type.")

    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File must be smaller than 15 MB.")

    temporary_path = None
    try:
        with NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
            temporary_file.write(content)
            temporary_path = temporary_file.name

        cleaned_question = question.strip()
        if not cleaned_question:
            raise HTTPException(status_code=400, detail="Enter a message.")
        return route_request(cleaned_question, temporary_path)
    except Exception as exc:
        print(f"PRISM file inference error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="PRISM could not process this file. Check the backend logs.",
        ) from exc
    finally:
        if temporary_path:
            Path(temporary_path).unlink(missing_ok=True)
