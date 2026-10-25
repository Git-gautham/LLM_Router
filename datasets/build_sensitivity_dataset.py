
from __future__ import annotations

import hashlib
import json
import random
import re
from itertools import islice
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import load_dataset


# ============================================================
# CONFIGURATION
# ============================================================

SEED = 42

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "datasets"
OUTPUT_DIR = DATA_DIR / "processed"

ALL_OUTPUT = OUTPUT_DIR / "sensitivity_dataset_all.csv"
TRAIN_OUTPUT = OUTPUT_DIR / "sensitivity_dataset_train.csv"
VAL_OUTPUT = OUTPUT_DIR / "sensitivity_dataset_val.csv"
TEST_OUTPUT = OUTPUT_DIR / "sensitivity_dataset_test.csv"
REVIEW_OUTPUT = OUTPUT_DIR / "review_queue.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "label_summary.csv"

LABELS = ["Public", "Internal", "Confidential", "Secret"]

# Generate more candidates than needed so deduplication does not
# leave any class short of the target size.
SYNTHETIC_PER_CLASS = 3500
TARGET_PER_CLASS = 2500

# Source limits prevent unexpectedly long downloads/processing.
PII_LIMIT = 5000
ENRON_LIMIT = 5000
DOLLY_LIMIT = 15000

PII_SHIELD_FILE = (
    "hf://datasets/auren-research/pii-shield/"
    "auren_privacy_annotated.parquet"
)

RNG = random.Random(SEED)


# ============================================================
# COMMON HELPERS
# ============================================================

def clean_text(value: Any) -> str:
    """Convert a value to clean, single-spaced text."""
    if value is None:
        return ""

    if isinstance(value, float) and pd.isna(value):
        return ""

    text = str(value)
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def text_hash(text: str) -> str:
    """Stable SHA-256 hash used for exact-text deduplication."""
    normalized = clean_text(text).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_json_list(value: Any) -> list[str]:
    """Parse a JSON list or comma-separated string safely."""
    if isinstance(value, list):
        return [clean_text(item) for item in value if clean_text(item)]

    if value is None:
        return []

    raw = clean_text(value)
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [
                clean_text(item)
                for item in parsed
                if clean_text(item)
            ]
    except (json.JSONDecodeError, TypeError):
        pass

    return [item.strip() for item in raw.split(",") if item.strip()]


def make_record(
    text: str,
    label: str,
    source: str,
    label_reason: str,
    confidence: float,
    review_required: bool = False,
    pii_types: list[str] | None = None,
) -> dict[str, Any] | None:
    """Create a consistent dataset record."""
    text = clean_text(text)

    if len(text) < 20:
        return None

    if label not in LABELS:
        return None

    return {
        "text": text,
        "label": label,
        "source": source,
        "label_reason": label_reason,
        "label_confidence": confidence,
        "review_required": bool(review_required),
        "pii_types": json.dumps(pii_types or [], ensure_ascii=False),
        "text_hash": text_hash(text),
    }


def safe_load_rows(
    description: str,
    loader,
    limit: int,
) -> list[dict[str, Any]]:
    """
    Load a bounded number of records.

    A source failure is reported without stopping the other sources.
    """
    print(f"\nLoading {description}...")

    try:
        dataset = loader()
        rows = list(islice(iter(dataset), limit))
        print(f"{description}: loaded {len(rows):,} rows")
        return rows
    except Exception as exc:
        print(f"WARNING: Could not load {description}.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        return []


# ============================================================
# 1. PII SHIELD
# ============================================================

def load_pii_shield() -> list[dict[str, Any]]:
    """
    PII Shield is a PII-detection dataset, not a four-class
    sensitivity dataset.

    Its records are placed in the review queue. We do not
    automatically equate PII with Confidential or Secret.
    """

    def primary_loader():
        return load_dataset(
            "parquet",
            data_files={"train": PII_SHIELD_FILE},
            split="train",
            streaming=True,
        )

    def fallback_loader():
        # Fallback for repositories/configurations that expose
        # the English split through the dataset builder.
        return load_dataset(
            "auren-research/pii-shield",
            "en",
            split="train",
            streaming=True,
        )

    rows = safe_load_rows(
        "PII Shield (direct Parquet path)",
        primary_loader,
        PII_LIMIT,
    )

    if not rows:
        rows = safe_load_rows(
            "PII Shield (English configuration fallback)",
            fallback_loader,
            PII_LIMIT,
        )

    records = []

    for row in rows:
        text = clean_text(row.get("text", ""))
        if not text:
            continue

        has_pii = row.get("has_pii", None)
        pii_types = parse_json_list(row.get("pii_types", []))

        # The dataset's PII annotation does not reliably establish
        # the organizational sensitivity level. Keep it for review.
        if has_pii is True or str(has_pii).lower() == "true":
            candidate_label = "Confidential"
            reason = (
                "PII Shield indicates PII; Confidential is only a "
                "review candidate, not an accepted training label."
            )
        else:
            candidate_label = "Public"
            reason = (
                "PII Shield does not indicate PII; this alone does "
                "not prove that the content is Public."
            )

        record = make_record(
            text=text,
            label=candidate_label,
            source="pii_shield",
            label_reason=reason,
            confidence=0.0,
            review_required=True,
            pii_types=pii_types,
        )

        if record:
            records.append(record)

    print(f"PII Shield review candidates: {len(records):,}")
    return records


# ============================================================
# 2. ENRON EMAILS
# ============================================================

def load_enron() -> list[dict[str, Any]]:
    """
    Enron emails may contain business-sensitive information,
    but the source alone does not establish a reliable
    Public/Internal/Confidential/Secret label.
    """

    def loader():
        return load_dataset(
            "corbt/enron-emails",
            split="train",
            streaming=True,
        )

    rows = safe_load_rows("Enron emails", loader, ENRON_LIMIT)
    records = []

    for row in rows:
        subject = clean_text(row.get("subject", ""))
        body = clean_text(row.get("body", ""))

        text = f"Subject: {subject}\n\n{body}".strip()
        if len(text) < 20:
            continue

        record = make_record(
            text=text,
            label="Internal",
            source="enron_emails",
            label_reason=(
                "Business email candidate. Internal is a provisional "
                "label and requires human review."
            ),
            confidence=0.0,
            review_required=True,
            pii_types=[],
        )

        if record:
            records.append(record)

    print(f"Enron review candidates: {len(records):,}")
    return records


# ============================================================
# 3. DOLLY INSTRUCTION DATA
# ============================================================

def load_dolly() -> list[dict[str, Any]]:
    """
    Dolly is used as a source of public-style instruction examples.
    The Public label is provisional: check examples before relying
    on them for a real privacy decision.
    """

    def loader():
        return load_dataset(
            "databricks/databricks-dolly-15k",
            split="train",
            streaming=True,
        )

    rows = safe_load_rows("Dolly instruction data", loader, DOLLY_LIMIT)
    records = []

    for row in rows:
        instruction = clean_text(row.get("instruction", ""))
        context = clean_text(row.get("context", ""))
        response = clean_text(row.get("response", ""))

        parts = []
        if instruction:
            parts.append(f"Instruction: {instruction}")
        if context:
            parts.append(f"Context: {context}")
        if response:
            parts.append(f"Response: {response}")

        text = "\n".join(parts).strip()
        if len(text) < 20:
            continue

        record = make_record(
            text=text,
            label="Public",
            source="dolly",
            label_reason=(
                "Public-style instruction example; source-derived "
                "label is provisional and should be reviewed."
            ),
            confidence=0.65,
            review_required=False,
            pii_types=[],
        )

        if record:
            records.append(record)

    print(f"Dolly Public candidates: {len(records):,}")
    return records


# ============================================================
# 4. SYNTHETIC DATA GENERATION
# ============================================================

PUBLIC_TOPICS = [
    "photosynthesis",
    "basic algebra",
    "the water cycle",
    "healthy study habits",
    "the history of printing",
    "recycling household waste",
    "public transport planning",
    "introductory astronomy",
    "soil conservation",
    "renewable energy",
    "library organization",
    "weather forecasting",
    "basic computer networking",
    "ocean ecosystems",
    "clear technical writing",
    "time management",
    "safe food storage",
    "the scientific method",
    "local tourism",
    "plant growth",
]

PUBLIC_TASKS = [
    "Write a short explanation of {topic}.",
    "Prepare a beginner-friendly summary about {topic}.",
    "Create three study questions about {topic}.",
    "Explain the main ideas behind {topic} for a general audience.",
    "Draft a neutral educational paragraph about {topic}.",
    "List practical examples that help explain {topic}.",
    "Summarize the basic principles of {topic}.",
    "Create a short classroom activity about {topic}.",
]

INTERNAL_DEPARTMENTS = [
    "operations",
    "customer support",
    "engineering",
    "marketing",
    "finance",
    "human resources",
    "quality assurance",
    "logistics",
    "product development",
    "IT services",
    "procurement",
    "facilities",
]

INTERNAL_TASKS = [
    "The {department} team will review the draft schedule before the weekly meeting.",
    "Please share the updated {department} checklist with the project group.",
    "The {department} meeting has moved to {day} at {time}.",
    "The project team recorded the following {department} action items for next week.",
    "Please keep the working notes for the {department} review within the team workspace.",
    "The {department} coordinator will circulate the revised process document tomorrow.",
    "The internal {department} status update is ready for the next team discussion.",
    "The {department} team needs feedback on the proposed workflow changes.",
    "The project owner asked the {department} group to confirm the open tasks.",
    "The {department} team will test the new process before wider rollout.",
]

CONFIDENTIAL_PROJECTS = [
    "Northstar",
    "Cedar",
    "Harbor",
    "Bluebird",
    "Orchard",
    "Summit",
    "Maple",
    "Lighthouse",
    "Willow",
    "Granite",
    "Meadow",
    "Aurora",
]

CONFIDENTIAL_FIELDS = [
    "quarterly revenue forecast",
    "unreleased product schedule",
    "employee compensation review",
    "supplier pricing proposal",
    "customer account migration",
    "internal audit findings",
    "pending contract negotiation",
    "department budget revision",
    "planned acquisition assessment",
    "security remediation timeline",
    "customer retention analysis",
    "staffing and hiring plan",
]

CONFIDENTIAL_TASKS = [
    "The {project} project contains a draft of the {field}; share it only with the approved review group.",
    "Access to the {field} for project {project} should be limited to authorized team members.",
    "The project {project} review includes preliminary information about the {field}.",
    "Please do not distribute the {field} from {project} outside the assigned working group.",
    "The {project} working document summarizes the current {field} and remains under restricted review.",
    "The team is validating the {field} for {project} before a decision is announced.",
    "A draft covering the {field} was added to the restricted {project} workspace.",
    "The {field} in the {project} planning notes has not been approved for external release.",
    "Please confirm the recipient list before sharing the {project} {field}.",
    "The {project} team is reviewing assumptions in the {field} prior to publication.",
]

SECRET_SYSTEMS = [
    "staging-api",
    "billing-service",
    "document-store",
    "identity-gateway",
    "reporting-worker",
    "internal-dashboard",
    "deployment-agent",
    "backup-service",
    "customer-sync",
    "build-runner",
    "data-pipeline",
    "admin-console",
]

SECRET_USERS = [
    "service_reader",
    "batch_worker",
    "release_agent",
    "reporting_bot",
    "integration_user",
    "deployment_bot",
    "backup_operator",
    "service_account",
    "sync_worker",
    "build_service",
]

SECRET_TASKS = [
    "The {system} configuration contains the production credential for account {user}: {credential}.",
    "A credential rotation note for {system} lists {user} with token {credential}; restrict access to the secret store.",
    "The deployment record for {system} includes the private access value {credential} assigned to {user}.",
    "The {system} service configuration contains password material for {user}: {credential}.",
    "The incident notes include the exposed access token {credential} for {system}; revoke it and use the approved vault.",
    "The restricted operations record lists {user} and the authentication secret {credential} for {system}.",
    "The {system} integration uses this private API key for {user}: {credential}.",
    "The backup configuration stores the sensitive authentication value {credential} for {system}.",
    "The {system} access record contains a private key reference for {user}: {credential}.",
    "The {system} runbook includes a temporary secret {credential} for the {user} account.",
]

DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]

TIMES = [
    "09:00", "09:30", "10:00", "10:30", "11:00",
    "13:00", "13:30", "14:00", "15:00", "16:00",
]

# These are fake placeholders, not real credentials.
FAKE_CREDENTIALS = [
    "DEMO_KEY_ALPHA_7X2",
    "SAMPLE_TOKEN_BETA_4Q9",
    "PLACEHOLDER_SECRET_GAMMA_8M1",
    "TEST_CREDENTIAL_DELTA_5R6",
    "EXAMPLE_PRIVATE_VALUE_EPSILON_3P8",
    "MOCK_API_TOKEN_ZETA_6K4",
    "FAKE_AUTH_VALUE_ETA_2W7",
    "DEVELOPMENT_ONLY_SECRET_THETA_9N5",
    "SYNTHETIC_KEY_IOTA_1C3",
    "NONPRODUCTION_TOKEN_KAPPA_4D8",
]

CONTEXT_ENDINGS = [
    "The note was prepared during routine project work.",
    "The latest version is stored in the team's working folder.",
    "Please verify the information before taking further action.",
    "The request was recorded during the current review cycle.",
    "The information was copied into the relevant project notes.",
    "The team will revisit the item during its next checkpoint.",
    "The entry was included in a routine status update.",
    "The current wording reflects the latest working draft.",
    "The record was created for the stated operational purpose.",
    "The owner should confirm the details before the next step.",
    "The team has not yet completed its review.",
    "The item remains part of the current work queue.",
]


def synthetic_text(label: str) -> str:
    """Generate a varied example for the requested class."""

    if label == "Public":
        topic = RNG.choice(PUBLIC_TOPICS)
        task = RNG.choice(PUBLIC_TASKS).format(topic=topic)
        return f"{task} {RNG.choice(CONTEXT_ENDINGS)}"

    if label == "Internal":
        department = RNG.choice(INTERNAL_DEPARTMENTS)
        task = RNG.choice(INTERNAL_TASKS).format(
            department=department,
            day=RNG.choice(DAYS),
            time=RNG.choice(TIMES),
        )
        return f"{task} {RNG.choice(CONTEXT_ENDINGS)}"

    if label == "Confidential":
        project = RNG.choice(CONFIDENTIAL_PROJECTS)
        field = RNG.choice(CONFIDENTIAL_FIELDS)
        task = RNG.choice(CONFIDENTIAL_TASKS).format(
            project=project,
            field=field,
        )
        return f"{task} {RNG.choice(CONTEXT_ENDINGS)}"

    if label == "Secret":
        system = RNG.choice(SECRET_SYSTEMS)
        user = RNG.choice(SECRET_USERS)
        credential = RNG.choice(FAKE_CREDENTIALS)
        task = RNG.choice(SECRET_TASKS).format(
            system=system,
            user=user,
            credential=credential,
        )
        return f"{task} {RNG.choice(CONTEXT_ENDINGS)}"

    raise ValueError(f"Unknown label: {label}")


def generate_synthetic_data() -> list[dict[str, Any]]:
    """
    Generate a varied candidate pool.

    Text diversity is improved with independent random choices.
    These examples are still synthetic and must not be mistaken
    for real-world, human-verified privacy labels.
    """
    records = []
    seen_hashes = set()

    for label in LABELS:
        accepted = 0
        attempts = 0
        max_attempts = SYNTHETIC_PER_CLASS * 30

        while (
            accepted < SYNTHETIC_PER_CLASS
            and attempts < max_attempts
        ):
            attempts += 1
            text = synthetic_text(label)
            digest = text_hash(text)

            if digest in seen_hashes:
                continue

            seen_hashes.add(digest)

            record = make_record(
                text=text,
                label=label,
                source="synthetic",
                label_reason=(
                    "Programmatically generated example. "
                    "Label is assigned by its generation template."
                ),
                confidence=0.75,
                review_required=False,
                pii_types=[],
            )

            if record:
                records.append(record)
                accepted += 1

        print(
            f"Synthetic {label}: {accepted:,} unique examples "
            f"(requested {SYNTHETIC_PER_CLASS:,})"
        )

    return records


# ============================================================
# 5. DEDUPLICATION AND BALANCED DATASET
# ============================================================

def deduplicate_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deduplicate by normalized text hash."""
    seen = set()
    result = []

    for record in records:
        digest = record.get("text_hash") or text_hash(record["text"])

        if digest in seen:
            continue

        seen.add(digest)
        result.append(record)

    return result


def build_balanced_training_set(
    records: list[dict[str, Any]],
) -> pd.DataFrame:
    """
    Use only records not marked for review, then sample the same
    number of rows from each class.

    Dolly Public rows and synthetic Public rows can both be used.
    Enron and PII Shield rows remain excluded until reviewed.
    """
    eligible = [
        record
        for record in records
        if not record["review_required"]
        and record["label"] in LABELS
    ]

    by_label = {
        label: [
            record for record in eligible
            if record["label"] == label
        ]
        for label in LABELS
    }

    print("\nEligible examples before balancing:")
    for label in LABELS:
        print(f"  {label}: {len(by_label[label]):,}")

    # A balanced dataset cannot contain more examples per class
    # than the smallest eligible class.
    available_minimum = min(
        len(by_label[label]) for label in LABELS
    )

    target = min(TARGET_PER_CLASS, available_minimum)

    if target == 0:
        raise RuntimeError(
            "At least one label has no eligible examples. "
            "Check synthetic generation and source-loading errors."
        )

    if target < TARGET_PER_CLASS:
        print(
            f"\nWARNING: Target reduced from {TARGET_PER_CLASS} "
            f"to {target} per class because a class has fewer "
            "eligible examples."
        )

    sampled = []

    for label in LABELS:
        label_rows = by_label[label].copy()
        RNG.shuffle(label_rows)
        sampled.extend(label_rows[:target])

    RNG.shuffle(sampled)

    result = pd.DataFrame(sampled)
    result = result.drop_duplicates(subset=["text_hash"]).reset_index(drop=True)

    print(f"\nBalanced eligible rows: {len(result):,}")
    print("Balanced class counts:")
    print(result["label"].value_counts().reindex(LABELS, fill_value=0))

    return result


def stratified_split(
    balanced_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create deterministic, per-class 80/10/10 splits."""
    train_parts = []
    val_parts = []
    test_parts = []

    for label in LABELS:
        group = balanced_df[balanced_df["label"] == label].copy()

        # Sort first so the seeded shuffle is reproducible.
        group = group.sort_values("text_hash").reset_index(drop=True)

        indices = list(range(len(group)))
        RNG.shuffle(indices)
        group = group.iloc[indices].reset_index(drop=True)

        count = len(group)
        train_end = int(count * 0.80)
        val_end = int(count * 0.90)

        train_parts.append(group.iloc[:train_end])
        val_parts.append(group.iloc[train_end:val_end])
        test_parts.append(group.iloc[val_end:])

    train_df = pd.concat(train_parts, ignore_index=True)
    val_df = pd.concat(val_parts, ignore_index=True)
    test_df = pd.concat(test_parts, ignore_index=True)

    # Shuffle across classes without changing the split membership.
    train_df = train_df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    val_df = val_df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    test_df = test_df.sample(frac=1, random_state=SEED).reset_index(drop=True)

    return train_df, val_df, test_df


# ============================================================
# 6. SAVE OUTPUTS AND SUMMARIES
# ============================================================

def save_outputs(
    all_records: list[dict[str, Any]],
    training_df: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_df = pd.DataFrame(all_records)

    if not all_df.empty:
        all_df = all_df.drop_duplicates(
            subset=["text_hash"]
        ).reset_index(drop=True)

    review_df = all_df[
        all_df["review_required"].astype(bool)
    ].copy() if not all_df.empty else pd.DataFrame()

    train_df, val_df, test_df = stratified_split(training_df)

    all_df.to_csv(ALL_OUTPUT, index=False, encoding="utf-8-sig")
    train_df.to_csv(TRAIN_OUTPUT, index=False, encoding="utf-8-sig")
    val_df.to_csv(VAL_OUTPUT, index=False, encoding="utf-8-sig")
    test_df.to_csv(TEST_OUTPUT, index=False, encoding="utf-8-sig")
    review_df.to_csv(REVIEW_OUTPUT, index=False, encoding="utf-8-sig")

    # Summary of all retained candidates, including review rows.
    if not all_df.empty:
        summary = (
            all_df.groupby(["source", "label"], dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(["label", "source"])
        )
        summary.to_csv(SUMMARY_OUTPUT, index=False, encoding="utf-8-sig")

    print("\n============================================================")
    print("DATASET BUILD COMPLETE")
    print("============================================================")
    print(f"All candidates : {ALL_OUTPUT} ({len(all_df):,} rows)")
    print(f"Training set   : {TRAIN_OUTPUT} ({len(train_df):,} rows)")
    print(f"Validation set : {VAL_OUTPUT} ({len(val_df):,} rows)")
    print(f"Test set       : {TEST_OUTPUT} ({len(test_df):,} rows)")
    print(f"Review queue   : {REVIEW_OUTPUT} ({len(review_df):,} rows)")
    print(f"Label summary  : {SUMMARY_OUTPUT}")

    for name, frame in [
        ("TRAIN", train_df),
        ("VALIDATION", val_df),
        ("TEST", test_df),
    ]:
        print(f"\n{name} label counts:")
        print(frame["label"].value_counts().reindex(LABELS, fill_value=0))


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print("Building privacy sensitivity dataset...")
    print(f"Project directory: {ROOT_DIR}")
    print(f"Random seed: {SEED}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pii_records = load_pii_shield()
    enron_records = load_enron()
    dolly_records = load_dolly()
    synthetic_records = generate_synthetic_data()

    # All candidates are retained for inspection. Only records
    # marked review_required=False can enter the training pool.
    all_records = (
        pii_records
        + enron_records
        + dolly_records
        + synthetic_records
    )

    all_records = deduplicate_records(all_records)

    print(f"\nAll unique candidate records: {len(all_records):,}")

    training_df = build_balanced_training_set(all_records)

    save_outputs(all_records, training_df)


if __name__ == "__main__":
    main()
