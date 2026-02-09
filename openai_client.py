from openai import OpenAI

client = OpenAI()

def ask_openai(parsed_error: dict, code: str) -> str:
    prompt = f"""
You are a senior backend engineer.

An error occurred in a production system.

Parsed error info:
{parsed_error}

Here is the related code:
{code}

Explain:
1. What is causing the error
2. Which file/function is responsible
3. How to fix it (step by step)
4. Provide corrected code if possible
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert software debugger."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
