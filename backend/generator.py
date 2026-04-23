# generator.py
# Responsibility: Given a query + retrieved context, call an LLM and get an answer.

import requests
import config


def build_prompt(query: str, context_chunks: list[dict]) -> str:
    """
    Build a compact, effective prompt.
    FIXES:
    - Limits context size (prevents truncation)
    - Encourages model to USE context
    """

    # ✅ LIMIT context (VERY IMPORTANT FIX)
    context_text = "\n\n".join(
        c["text"][:300]            # limit each chunk
        for c in context_chunks[:3]  # limit number of chunks
    )

    prompt = f"""
You are a helpful AI assistant.

Use the context below to answer the question clearly.
The answer is present in the context — summarize it.

Do NOT say "I don't have enough information" if any relevant information exists.

CONTEXT:
{context_text}

QUESTION:
{query}

ANSWER:
"""
    return prompt


def generate(query: str, context_chunks: list[dict]) -> dict:
    """
    Call the configured LLM provider.
    """
    prompt = build_prompt(query, context_chunks)

    if config.LLM_PROVIDER == "ollama":
        return _call_ollama(prompt)
    elif config.LLM_PROVIDER == "openai":
        return _call_openai(prompt)
    else:
        raise ValueError(f"Unknown LLM provider: {config.LLM_PROVIDER}")


def _call_ollama(prompt: str) -> dict:
    try:
        response = requests.post(
            config.OLLAMA_URL,
            json={
                "model": config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 128,
                    "num_ctx": 4096,   # ✅ INCREASED (important fix)
                }
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "").strip()

        return {
            "answer": answer,
            "tokens_used": data.get("eval_count", 0)
        }

    except requests.exceptions.ConnectionError:
        return {
            "answer": "Error: Ollama not running. Run: ollama serve",
            "tokens_used": 0
        }

    except requests.exceptions.Timeout:
        return {
            "answer": "Error: LLM timed out. Try a slightly larger model",
            "tokens_used": 0
        }

    except Exception as e:
        return {
            "answer": f"LLM Error: {str(e)}",
            "tokens_used": 0
        }


def _call_openai(prompt: str) -> dict:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_KEY)

        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=512
        )

        answer = response.choices[0].message.content.strip()

        return {
            "answer": answer,
            "tokens_used": response.usage.total_tokens
        }

    except Exception as e:
        return {
            "answer": f"OpenAI Error: {str(e)}",
            "tokens_used": 0
        }