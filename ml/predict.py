import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


MODEL_PATH = "./models/distilbert_router/checkpoint-24"
TOKENIZER_NAME = "distilbert-base-uncased"


class SensitivityClassifier:
    def __init__(
        self,
        model_path: str = MODEL_PATH,
        tokenizer_name: str = TOKENIZER_NAME,
    ):
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_path
        )

        self.model.eval()

    def predict(self, text: str) -> dict:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=128,
        )

        with torch.no_grad():
            outputs = self.model(**inputs)

        probabilities = torch.softmax(outputs.logits, dim=-1)[0]

        predicted_id = torch.argmax(probabilities).item()

        label = self.model.config.id2label[predicted_id]

        confidence = probabilities[predicted_id].item()

        return {
            "label": label,
            "confidence": round(confidence, 4),
        }


if __name__ == "__main__":
    classifier = SensitivityClassifier()

    test_inputs = [
        "What is machine learning?",
        "Summarize our internal software development process.",
        "Review this employee salary document.",
        "API_KEY=FAKE_API_KEY_123456789",
    ]

    print("Sensitivity Predictions")
    print("=" * 50)

    for text in test_inputs:
        result = classifier.predict(text)

        print(f"\nInput: {text}")
        print(f"Prediction: {result['label']}")
        print(f"Confidence: {result['confidence']}")