import ollama


def ask_local_llm(prompt: str) -> str:
    response = ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]


if __name__ == "__main__":
    prompt = "Explain machine learning in simple terms."

    answer = ask_local_llm(prompt)

    print("\nLocal LLM response:\n")
    print(answer)