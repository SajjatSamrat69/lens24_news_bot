import os
import json
import requests
from groq import Groq
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

gemini_client = genai.Client(
    api_key=GEMINI_API_KEY
)

groq_client = Groq(
    api_key=GROQ_API_KEY
)

PROMPT = """
আপনি বাংলাদেশের একজন পেশাদার সংবাদ সম্পাদক।

নিচের তথ্যের ভিত্তিতে ১৮০-২৫০ শব্দের একটি প্রমিত বাংলা সংবাদ লিখুন।

নিয়ম:

- শুধুমাত্র প্রদত্ত তথ্য ব্যবহার করুন।
- কোনো তথ্য, সংখ্যা বা উদ্ধৃতি তৈরি করবেন না।
- ৩-৪টি স্বাভাবিক অনুচ্ছেদ লিখুন।
- প্রথম অনুচ্ছেদে মূল ঘটনা লিখুন।
- শেষ অনুচ্ছেদে ঘটনার গুরুত্ব লিখুন।
- ভাষা হবে স্বাভাবিক, সাবলীল ও সংবাদপত্র উপযোগী বাংলা।
- কোনো ইংরেজি অনুচ্ছেদ লিখবেন না।
- শুধুমাত্র সংবাদ লিখুন।

বিভাগ:
{category}

শিরোনাম:
{title}

তথ্য:
{article}
"""

def gemini_rewrite(prompt):
    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config={
                "temperature": 0.1,
                "max_output_tokens": 2048,
            }
        )

        if response.text:
            return response.text.strip()

        raise Exception("Empty Gemini response")

    except Exception as e:
        print("Gemini failed:", e)
        return None


def groq_rewrite(prompt):
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_completion_tokens=2048,
            top_p=1,
            stream=False
        )

        return completion.choices[0].message.content.strip()

    except Exception as e:
        print("Groq failed:", e)
        return None


def openrouter_rewrite(prompt):
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com",
                "X-OpenRouter-Title": "Lens24 News Bot"
            },
            json={
                "model": "deepseek/deepseek-chat-v3",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 2048
            },
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("OpenRouter failed:", e)
        return None



def rewrite(prompt):
    # 1. Gemini
    result = gemini_rewrite(prompt)
    if result:
        print("✓ Used Gemini")
        return result

    # 2. Groq
    result = groq_rewrite(prompt)
    if result:
        print("✓ Used Groq")
        return result

    # 3. OpenRouter
    result = openrouter_rewrite(prompt)
    if result:
        print("✓ Used OpenRouter")
        return result

    raise Exception("All AI providers failed.")
